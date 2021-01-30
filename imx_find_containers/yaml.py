import abc
import functools
from . import imx
from . import fit


# Initialize module YAML variables
_yaml = None
_use_yaml = False
_open_yaml = None
_write_yaml = None


def find_types_with_custom_yaml_repr():
    # Get custom types from the iMX module
    typ_list = [t for t in (getattr(imx, a) for a in dir(imx)) if hasattr(t, 'yaml_tag')]

    # Get custom types from the FIT module
    typ_list += [t for t in (getattr(fit, a) for a in dir(fit)) if hasattr(t, 'yaml_tag')]

    return typ_list


class YamlIface(abc.ABC):
    def __init__(self):
        self._types_initialized = False
        self.yaml = None
        self.loader = None
        self.dumper = None

    def register_custom_types(self):
        # Register all of the classes with custom yaml export functions
        for typ in find_types_with_custom_yaml_repr():
            if hasattr(self.yaml, 'register_class'):
                self.yaml.register_class(typ)
            else:
                self.dumper.add_representer(typ, typ.to_yaml)
                self.loader.add_constructor(typ.yaml_tag, typ.from_yaml)

        # Customize int to always be saved as a hex value (makes scan results 
        # easier to read directly)
        def hexint_presenter(representer, data):
            return representer.represent_int(hex(data))
        self.dumper.add_representer(int, hexint_presenter)

        # Custom representation for the range type
        def range_presenter(representer, data):
            range_str = f'({data.start:#x}, {data.stop:#x}, {data.step:#x})'
            return representer.represent_scalar('!range', range_str)
        self.dumper.add_representer(range, range_presenter)

        # The custom range output format needs a custom constructor also
        def range_constructor(constructor, node):
            start, stop, step = [int(v, 16) for v in node.value[1:-1].split(', ')]
            return range(start, stop, step)
        self.loader.add_constructor('!range', range_constructor)

    def register_types(wrapped_func):
        @functools.wraps(wrapped_func)
        def register_types_wrapper(self, *args, **kwargs):
            if not self._types_initialized:
                self.register_custom_types()
                self._types_initialized = True
            return wrapped_func(self, *args, **kwargs)
        return register_types_wrapper

    @abc.abstractmethod
    def open(self, filename):
        pass

    @abc.abstractmethod
    def write(self, filename, results):
        pass


class RuamelYamlIface(YamlIface):
    def __init__(self):
        super().__init__()
        import ruamel.yaml
        self.yaml = ruamel.yaml.YAML(typ='unsafe')
        self.dumper = self.yaml.representer
        self.loader = self.yaml.constructor

    @YamlIface.register_types
    def open(self, filename):
        with open(filename, 'r') as f:
            return self.yaml.load(f)
        with open(filename, 'r') as f:
            loader = self.loader(f)
            return loader._constructor.get_single_data()

    @YamlIface.register_types
    def write(self, filename, results):
        full_filename = f'{filename}.yaml'
        print(f'Saving scan results: {full_filename}')

        with open(full_filename, 'w') as f:
            self.yaml.dump(results, f)

        # Return the filename
        return full_filename


class PyYamlIface(YamlIface):
    def __init__(self):
        super().__init__()
        import yaml as pyyaml
        self.yaml = pyyaml

        try:
            self.dumper = pyyaml.CDumper
        except AttributeError:
            self.dumper = pyyaml.Dumper

        try:
            self.loader = pyyaml.CUnsafeLoader
        except AttributeError:
            self.loader = pyyaml.UnsafeLoader

    @YamlIface.register_types
    def open(self, filename):
        with open(filename, 'r') as f:
            return self.yaml.load(f, Loader=self.loader)

    @YamlIface.register_types
    def write(self, filename, results):
        full_filename = f'{filename}.yaml'
        print(f'Saving scan results: {full_filename}')

        output = self.yaml.dump(results, Dumper=self.dumper)
        with open(full_filename, 'w') as f:
            f.write(output)

        # Return the filename
        return full_filename


# First option to check is PyYAML, it's more widely used and faster
# These iface "name" strings match the output format choices in main()
modules = {
    'PyYAML': PyYamlIface,
    'ruamel.yaml': RuamelYamlIface,
}


# Caching available yaml modules
available_modules = None


def get_yaml_modules_available():
    global available_modules, modules
    if available_modules is None:
        available_modules = {}
        for name, iface in modules.items():
            try:
                available_modules[name] = iface()
            except ImportError:
                pass

        # If at least one YAML interface was created assign the first one to the 
        # generic "yaml" output format
        if available_modules:
            first_avail = next(iter(available_modules))
            available_modules['yaml'] = available_modules[first_avail]

    return available_modules


__all__ = [
    'get_yaml_modules_available',
]
