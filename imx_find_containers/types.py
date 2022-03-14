import enum
import struct
import functools
import operator
import abc


# To make yaml_tag in the ExportableEnum class a function instead of static
class classproperty:
    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        self.fget = fget
        self.fset = fset
        self.fdel = fdel
        if doc is None and fget is not None:
            doc = fget.__doc__
        self.__doc__ = doc

    def __get__(self, instance, ownerclass):
        return self.fget(ownerclass)


class ExportableIntEnum(enum.IntEnum):
    @classproperty
    def yaml_tag(cls):
        return f'!{cls.__name__}'

    @classmethod
    def to_yaml(cls, representer, node):
        enum_str = f'{node.name} ({node.value:#x})'
        return representer.represent_scalar(cls.yaml_tag, enum_str)

    @classmethod
    def from_yaml(cls, constructor, node):
        val_name, _ = node.value.split()
        return cls[val_name]


class ExportableIntFlag(enum.IntFlag):
    @classproperty
    def yaml_tag(cls):
        return f'!{cls.__name__}'

    @classmethod
    def to_yaml(cls, representer, node):
        # I'd _like_ to just have this be a straight repr(node) but that
        # produces a value that is very difficult to import.
        bits = [f for f in list(cls) if f & node.value]
        bit_name_list = '|'.join(f.name for f in bits)
        bit_val_list = '|'.join(str(f.value) for f in bits)
        enum_flag_str = f'{bit_name_list} ({bit_val_list})'
        return representer.represent_scalar(cls.yaml_tag, enum_flag_str)

    @classmethod
    def from_yaml(cls, constructor, node):
        _, values_str = node.value.split()
        # take the numerical values between the parenthesis and combine them
        # into a single value
        values_list = [int(v) for v in values_str[1:-1].split('|')]
        value = functools.reduce(operator.ior, values_list)
        return cls(value)


class ExportableObject:
    @classproperty
    def yaml_tag(cls):
        return f'!{cls.__name__}'

    @classmethod
    def to_yaml(cls, representer, node):
        if hasattr(node, 'get_yaml_attrs'):
            value = dict((a, getattr(node, a)) for a in node.get_yaml_attrs())
        else:
            value = dict((k, v) for k, v in vars(node).items() if not k.startswith('_'))
        return representer.represent_mapping(cls.yaml_tag, value, flow_style=False)

    @classmethod
    def from_yaml(cls, constructor, node):
        data = constructor.construct_mapping(node, deep=True)
        return cls(**data)


class StructTuple(ExportableObject):
    _struct = None
    _fields = None

    @classproperty
    def size(cls):
        return cls._struct.size

    def __init__(self, data=None, offset=0, **kwargs):
        # Must have some arguments
        assert data is not None or kwargs

        if data is not None:
            assert len(data[offset:]) >= self.size
            unpacked = self._struct.unpack_from(data, offset=offset)
            for attr, arg in zip(self._fields, unpacked):
                setattr(self, attr, arg)
        elif kwargs:
            assert all(attr in kwargs for attr in self._fields)
            for attr in self._fields:
                setattr(self, attr, kwargs[attr])

    def __repr__(self):
        attrs = []
        for key in self._fields:
            value = getattr(self, key)
            try:
                attrs.append(f'{key}={value:#x}')
            except TypeError:
                # Default to __repr__ of the value
                attrs.append(f'{key}={value:r}')
        param_str = ', '.join(attrs)
        return f'{self.__class__.__name__}({param_str})'

    def __iter__(self):
        return iter(self._fields)

    def __contains__(self, key):
        return key in self._fields

    def __getitem__(self, key):
        if key not in self:
            raise KeyError
        return getattr(self, key)


class StructTupleMeta(type):
    def __new__(metacls, cls, bases, classdict):
        _struct = struct.Struct(classdict.pop('fmt'))
        _fields = classdict.pop('fields')

        classdict['_struct'] = _struct
        classdict['_fields'] = _fields

        newtyp_bases = (StructTuple,) + bases

        newtyp = super().__new__(metacls, cls, newtyp_bases, classdict)

        return newtyp


class Container(ExportableObject, abc.ABC):
    @classmethod
    @abc.abstractmethod
    def is_container(cls, data, offset, verbose=False):
        raise NotImplementedError

    def __init__(self, data=None, offset=0, export_images=False, verbose=False, **kwargs):
        assert data or kwargs

        # This option defines whether or not any "images" are included in a yaml
        # export
        self._export_images = export_images

        self._verbose = verbose
        self.offset = offset
        self.images = []

        if data is not None:
            self.init_from_data(data, offset)
        else:
            # Recreating a loaded object, probably from a scan results file.
            # each key=value pair is an attribute and value that should be set
            for key, value in kwargs.items():
                setattr(self, key, value)

        # Handle mapping any image data now
        if hasattr(self, 'images') and self.images and isinstance(self.images, (list, tuple)):
            self.map_images_by_addr()

    def __iter__(self):
        # Make it easy to iterate over the available info in a container, the
        # iterator returns a list of properties that can be accessed.
        return (a for a in vars(self) if not a.startswith('_'))

    def __contains__(self, key):
        return key in iter(self)

    def __getitem__(self, key):
        # Allow accessing container attributes like a dictionary but only
        # non-hidden properties to match the keys returned by the __iter__
        # function.
        if key not in self:
            raise KeyError
        return getattr(self, key)

    @property
    def export_images(self):
        return self._export_images

    @export_images.setter
    def export_images(self, value):
        self._export_images = value

    def get_yaml_attrs(self):
        if self.export_images:
            return (k for k in vars(self).keys() if not k.startswith('_'))
        else:
            return (k for k in vars(self).keys() if not k.startswith('_') and k != 'images')

    @abc.abstractmethod
    def init_from_data(self, data, offset):
        raise NotImplementedError

    def map_images_by_addr(self):
        # Any container-specific data processing should happen before this
        # function is called

        # For ease of identifying which image belongs to which addresses, map
        # them out now
        self._image_addrs = {}
        for img in self.images:
            if img['range'] is not None:
                self._image_addrs[img['range']] = img

    def find_image_by_addr(self, addr):
        # If the address provided is in the address range of one of the images
        # in this container, the image info is returned
        for addr_range, img in self._image_addrs.items():
            if addr in addr_range:
                return img
        return None

    def find_next_addr(self, addr):
        # A utility to find the next address that is not in an image belonging
        # to this container
        img = self.find_image_by_addr(addr)
        if img is None:
            return addr
        else:
            # Find the address that is at the end of the identified image, and
            # ensure that doesn't match any other images in this container
            next_addr = img['range'].stop
            return self.find_next_addr(next_addr)

    def __repr__(self):
        if hasattr(self, 'hdr'):
            param_str = repr(self.hdr)
        else:
            param_str = 'None'

        return f'{self.__class__.__name__}({param_str})'

    def __str__(self):
        return f'{self.offset:#08x}: {repr(self)}'


__all__ = [
    'classproperty',
    'ExportableIntEnum',
    'ExportableIntFlag',
    'ExportableObject',
    'StructTuple',
    'StructTupleMeta',
    'Container',
]
