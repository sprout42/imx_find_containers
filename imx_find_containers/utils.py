import re
import os
import enum
import time

from .types import StructTuple
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


def _write_yaml(filename, results, include_image_contents=False):
    import ruamel.yaml
    yaml = ruamel.yaml.YAML()

    # Register all of the enum classes with custom yaml export functions
    for obj in vars(imx).values():
        if hasattr(obj, 'to_yaml'):
            yaml.register_class(obj)

    # Customize how the yaml output will look
    def hexint_presenter(representer, data):
        return representer.represent_int(hex(data))
    yaml.representer.add_representer(int, hexint_presenter)

    def range_presenter(representer, data):
        range_str = f'({data.start:#x}, {data.stop:#x}, {data.step:#x})'
        return representer.represent_scalar('!range', range_str)
    yaml.representer.add_representer(range, range_presenter)

    def container_presenter(representer, container):
        obj = []
        for key, val in container.export().items():
            # only include the images in the scan results if the 
            # include_image_contents flag is set
            if key != 'images' or (key == 'images' and include_image_contents):
                obj.append((representer.represent_data(key), representer.represent_data(val)))
        return ruamel.yaml.nodes.MappingNode(u'tag:yaml.org,2002:map', obj)
    yaml.representer.add_representer(imx.iMXImageContainer, container_presenter)
    yaml.representer.add_representer(fit.FITContainer, container_presenter)

    with open(f'{filename}.yaml', 'w') as f:
        yaml.dump(results, f)


def _write_pickle(filename, results):
    # Some nasty private variable hacks to make these classes pickle-able
    for obj in vars(imx).values():
        if isinstance(obj, StructTuple):
            obj._namedtuple.__qualname__ = f'{obj._name}._namedtuple'

    import pickle
    with open(f'{filename}.pickle', 'wb') as f:
        pickle.dump(results, f)


def _open_yaml(filename):
    # ruamel.yaml works better with python3, but PyYAML should work ok as well 
    # for this
    try:
        import ruamel.yaml as yaml
    except ImportError:
        import yaml

    try:
        from yaml import CLoader as yamlLoader
    except ImportError:
        from yaml import Loader as yamlLoader

    with open(filename, 'r') as f:
        return yaml.load(f, Loader=yamlLoader)


def _open_pickle(filename):
    import pickle
    with open(filename, 'rb') as f:
        return pickle.load(f)


def open_results(filename):
    try:
        return _open_pickle(filename)
    except pickle.UnpicklingError:
        return _open_yaml(filename)


def _path_to_filename(path):
    filename = re.sub(r'/', '_', path)
    # Remove any leading '._' string if it is present
    filename = filename.lstrip('._')
    return filename


def export(results, include_image_contents=False, extract=False, **kwargs):
    export_filename = time.strftime("scan_results.%Y-%m-%dT%H:%M:%S%z", time.localtime())

    # First save the overall results
    #_write_pickle(export_filename, results)
    print(f'Saving scan results: {export_filename}')
    _write_yaml(export_filename, results, include_image_contents)

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
