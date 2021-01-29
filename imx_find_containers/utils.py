import re
import os
import enum
import time

# pickle is the backup results saving option
import pickle
try:
    import ruamel.yaml
    _use_yaml = True
except ImportError:
    _use_yaml = False

from . import imx
from . import fit


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


def _write_yaml(filename, results):
    yaml = ruamel.yaml.YAML()

    # Register all of the enum classes with custom yaml export functions
    for obj in vars(imx).values():
        if hasattr(obj, 'yaml_tag'):
            yaml.register_class(obj)

    for obj in vars(fit).values():
        if hasattr(obj, 'yaml_tag'):
            yaml.register_class(obj)

    # Customize how the yaml output will look
    def hexint_presenter(representer, data):
        return representer.represent_int(hex(data))
    yaml.representer.add_representer(int, hexint_presenter)

    def range_presenter(representer, data):
        range_str = f'({data.start:#x}, {data.stop:#x}, {data.step:#x})'
        return representer.represent_scalar('!range', range_str)
    yaml.representer.add_representer(range, range_presenter)

    full_filename = f'{filename}.yaml'
    print(f'Saving scan results: {full_filename}')
    with open(full_filename, 'w') as f:
        yaml.dump(results, f)


def _write_pickle(filename, results):
    full_filename = f'{filename}.pickle'
    print(f'Saving scan results: {full_filename}')
    with open(full_filename, 'wb') as f:
        pickle.dump(results, f)


def _open_yaml(filename):
    # Use the "unsafe" loader so we get sane and easy to parse types from 
    # loading a doc
    yaml = ruamel.yaml.YAML(typ='unsafe')

    # Register all of the enum classes with custom yaml import functions
    for obj in vars(imx).values():
        if hasattr(obj, 'yaml_tag'):
            yaml.register_class(obj)

    for obj in vars(fit).values():
        if hasattr(obj, 'yaml_tag'):
            yaml.register_class(obj)

    # The custom range output also has to be handled
    def range_constructor(constructor, node):
        # The output in _write_yaml() is:
        #   (start, stop, step)
        # where the values are all base16
        #
        # Get the values in between the parenthesis and make a new range object
        start, stop, step = [int(v, 16) for v in node.value[1:-1].split(', ')]
        return range(start, stop, step)
    yaml.constructor.add_constructor('!range', range_constructor)

    with open(filename, 'r') as f:
        return yaml.load(f)


def _open_pickle(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)


def open_results(filename):
    # The results being opened may be a yaml or a pickle
    try:
        return _open_pickle(filename)
    except pickle.UnpicklingError:
        return _open_yaml(filename)


def _path_to_filename(path):
    filename = re.sub(r'/', '_', path)
    # Remove any leading '._' string if it is present
    filename = filename.lstrip('._')
    return filename


def save_results(results, output_format=None, include_image_contents=False, extract=False, **kwargs):
    # First save the overall results
    export_filename = time.strftime("scan_results.%Y-%m-%dT%H:%M:%S%z", time.localtime())

    # Update the export_images flag in each container to indicate if they should 
    # be included in any exported results or not
    for filename in results:
        for container in results[filename]:
            container.export_images = include_image_contents

    if output_format == 'pickle' or not _use_yaml:
        _write_pickle(export_filename, results)
    else:
        _write_yaml(export_filename, results)

    # Now export any image files found binwalk-style
    if extract:
        for filename in results:
            for container in results[filename]:
                for img in container.images:
                    if img['data'] is not None:
                        if 'fileext' in img:
                            imgfilename = f'{_path_to_filename(filename)}--{offset:X}.{img["fileext"]}'
                        else:
                            offset = img['offset']
                            imgfilename = f'{_path_to_filename(filename)}-{offset:X}.bin'

                        # Handle writing out bytes or strings as determined by the 
                        # image type
                        print(f'Exporting image: {imgfilename}')
                        if isinstance(img['data'], bytes):
                            with open(imgfilename, 'wb') as f:
                                f.write(img['data'])
                        else:
                            with open(imgfilename, 'w') as f:
                                f.write(img['data'])


def recursive_scandir(path):
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


__all__ = [
    'open_results',
    'save_results',
    'recursive_scandir',
]
