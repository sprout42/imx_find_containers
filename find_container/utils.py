import enum
import time

from .types import StructTuple
from .imx import imx_types


def invert(num):
    # Only works on 1 byte values
    assert num <= 0xFF
    return num ^ 0xFF


def enum_or_int(enum_type, num):
    try:
        return enum_type(num)
    except ValueError:
        return num


def _normalize_obj(obj):
    if isinstance(obj, list):
        return [_normalize_obj(o) for o in obj]
    elif isinstance(obj, dict):
        return dict((k, _normalize_obj(v)) for k, v in obj.items())
    elif hasattr(obj, '__dict__') and not isinstance(obj, enum.Enum):
        # A standard class object
        return dict((k, _normalize_obj(v)) for k, v in vars(obj).items() if not k.startswith('_'))
    elif hasattr(obj, '_asdict'):
        # A namedtuple object
        return dict((k, _normalize_obj(v)) for k, v in obj._asdict().items() if not k.startswith('_'))
    else:
        # assume this is a normal value like an int or string
        return obj


def now():
    # return an ISO 8601 formatted date string
    # 2019-07-18T02:28:16+00:00
    return time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime())


def _write_yaml(filename, results):
    import ruamel.yaml
    yaml = ruamel.yaml.YAML()

    # Register all of the enum classes with custom yaml export functions
    for obj in vars(imx_types).values():
        if isinstance(obj, enum.Enum):
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
            obj.append((representer.represent_data(key), representer.represent_data(val)))
        return ruamel.yaml.nodes.MappingNode(u'tag:yaml.org,2002:map', obj)
    yaml.representer.add_representer(iMXImageContainer, container_presenter)

    with open(f'{filename}.yaml', 'w') as f:
        yaml.dump(results, f)


def _write_pickle(filename, results):
    # Some nasty private variable hacks to make these classes pickle-able
    for obj in vars(imx_types).values():
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


def export(results):
    export_filename = time.strftime("scan_results.%Y-%m-%dT%H:%M:%S%z", time.localtime())

    # First save the overall results
    #_write_pickle(export_filename, results)
    _write_yaml(export_filename, results)

    # Now export any image files found binwalk-style
    for filename in results:
        for container in results[filename]:
            for img in container.images:
                if img['data'] is not None:
                    offset = img['offset']
                    binname = f'{_path_to_filename(filename)}-{offset:X}.bin'
                    with open(binname, 'wb') as f:
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
