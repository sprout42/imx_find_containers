import re
import os
import enum
import time
import functools
import operator
import copy

# pickle is the backup results saving option
import pickle

from .types import Container, StructTuple

# YAML results saving utilities
from .yaml import *


def invert(num):
    # Only works on 1 byte values
    assert num <= 0xFF
    return num ^ 0xFF


def enum_or_int(enum_type, num):
    try:
        return enum_type(num)
    except ValueError:
        return num


def now():
    # return an ISO 8601 formatted date string
    # 2019-07-18T02:28:16+00:00
    return time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime())


def _write_pickle(filename, results, include_image_contents=False):
    # If include_image_contents is not set, make a duplicate of the results but 
    # delete the images and _image_addrs from the copy
    if not include_image_contents:
        export_results = copy.deepcopy(results)
        for container, _ in get_containers_from_results(export_results):
            if hasattr(container, '_image_addrs'):
                container._image_addrs = {}
            if hasattr(container, 'images'):
                container.images = []
    else:
        export_results = results

    full_filename = f'{filename}.pickle'
    print(f'Saving scan results: {full_filename}')
    with open(full_filename, 'wb') as f:
        pickle.dump(export_results, f)

    # Return the filename
    return full_filename


def _open_pickle(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)


def open_results(filename, output_format=None):
    # The results being opened may be a yaml or a pickle
    try:
        return _open_pickle(filename)
    except pickle.UnpicklingError:
        yaml_avail = get_yaml_modules_available()
        assert yaml_avail

        # Use the output_format to allow selection of which YAML module to use 
        # if there is a choice
        if output_format is not None:
            assert output_format in yaml_avail
            return yaml_avail[output_format].open(filename)
        else:
            return yaml_avail['yaml'].open(filename)


def _path_to_filename(path):
    filename = re.sub(r'/', '_', path)
    # Remove any leading '._' string if it is present
    filename = filename.lstrip('._')
    return filename


def container_save_images(container, prefix):
    if hasattr(container, 'images') and container.images is not None:
        for img in container.images:
            if img['data'] is not None:
                if 'fileext' in img:
                    imgfilename = f'{prefix}--{offset:X}.{img["fileext"]}'
                else:
                    offset = img['offset']
                    imgfilename = f'{prefix}-{offset:X}.bin'

                # Handle writing out bytes or strings as determined by the 
                # image type
                print(f'Exporting image: {imgfilename}')
                if isinstance(img['data'], bytes):
                    with open(imgfilename, 'wb') as f:
                        f.write(img['data'])
                else:
                    with open(imgfilename, 'w') as f:
                        f.write(img['data'])


def get_containers_from_results(results):
    # The results may be a dictionary, list, or single Container
    if isinstance(results, dict):
        # In this format the dict key is the filename that the data was 
        # extracted from and the value is a list of containers
        # TODO: someday I really should just use type annotations
        assert all( \
                isinstance(f, str) and \
                hasattr(r, '__iter__') and \
                all(isinstance(c, Container) for c in r) \
                for f, r in results.items())

        # In this format the key should be the source filename.
        # flatten the lists out
        containers = functools.reduce(operator.iconcat, \
                (((c, _path_to_filename(f)) for c in r) \
                for f, r in results.items()), [])
        return containers

    elif hasattr(results, '__iter__'):
        # Filename is unknown, use a placeholder prefix
        prefix = _path_to_filename('unknown')

        if all(isinstance(r, Container) for r in results):
            containers = ((r, prefix) for r in results)
            return containers

        elif all(hasattr(r, '__iter__') and \
                all(isinstance(c, Container) for c in r) \
                for r in results):
            containers = itertools.chain( \
                    ((c, prefix) for c in r) \
                    for r in results)
            return containers

    elif isinstance(results, Container):
        # Filename is unknown, use a placeholder prefix
        prefix = _path_to_filename('unknown')

        containers = list((results, prefix))
        return containers

    raise Exception(f'Unknown results format')


def save_images(results):
    containers = get_containers_from_results(results)
    for container, prefix in containers:
        container_save_images(container, prefix)


def save_results(results, output_format=None, include_image_contents=False, extract=False, **kwargs):
    # First save the overall results
    export_filename = time.strftime("scan_results.%Y-%m-%dT%H:%M:%S%z", time.localtime())

    # Update the export_images flag in each container to indicate if they should 
    # be included in any exported results or not
    containers = get_containers_from_results(results)
    for container, _ in containers:
        container.export_images = include_image_contents

    yaml_avail = get_yaml_modules_available()

    if output_format == 'auto':
        if yaml_avail:
            yaml_avail['yaml'].write(export_filename, results)
        else:
            _write_pickle(export_filename, results, include_image_contents)
    elif output_format == 'pickle':
        _write_pickle(export_filename, results, include_image_contents)
    else:
        # All other options should be in the yaml modules, if it isn't there 
        # throw an error
        assert output_format in yaml_avail
        yaml_avail[output_format].write(export_filename, results)

    if extract:
        # Now export any image files found binwalk-style
        for container, prefix in containers:
            container_save_images(container, prefix)

    # Return the filename the results were saved to
    return


def find_files(path):
    try:
        file_list = []
        for item in os.scandir(path):
            if item.is_file():
                file_list.append(item.path)
            elif item.is_dir():
                file_list.extend(recursive_scandir(item.path))
        return file_list
    except NotADirectoryError:
        return [path]


# Internal testing utilities
def cmp_value(s1, s2):
    if s1 != s2:
        raise AssertionError(f'{s1} != {s2}')
    return True


def cmp_dict(d1, d2):
    assert cmp_value(len(d1), len(d2))
    for key, value in d1.items():
        if key not in d2:
            raise AssertionError(f'{key} not in {list(d2.keys())}')
        assert cmp_objects(value, d2[key])
    return True


def cmp_objects(o1, o2):
    print(f'{o1.__class__.__name__} ?= {o2.__class__.__name__}')
    assert cmp_value(o1.__class__, o2.__class__)
    if isinstance(o1, (Container, StructTuple)):
        return cmp_dict(vars(o1), vars(o2))
    elif hasattr(o1, 'items'):
        return cmp_dict(o1, o2)
    elif isinstance(o1, (list, tuple)):
        assert cmp_value(len(o1), len(o2))
        for v1, v2 in zip(iter(o1), iter(o2)):
            assert cmp_objects(v1, v2)
    else:
        assert cmp_value(o1, o2)
    return True


__all__ = [
    'open_results',
    'save_results',
    'save_images',
    'find_files',
]
