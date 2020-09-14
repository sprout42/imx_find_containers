import enum
import struct
from collections import namedtuple


class StructTuple(object):
    def __init__(self, name, struct_str, fields):
        self._name = name
        self._struct = struct.Struct(struct_str)
        self._namedtuple = namedtuple(name, ' '.join(fields))

    @property
    def size(self):
        return self._struct.size

    def unpack(self, data):
        assert len(data) == self.size
        return self._namedtuple._make(self._struct.unpack(data))

    def unpack_from(self, data, offset=0):
        assert len(data[offset:]) >= self.size
        return self._namedtuple._make(self._struct.unpack_from(data, offset=offset))


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


class ContainerABC(object):
    @classmethod
    def is_container(cls, data, offset, verbose=False):
        raise NotImplementedError

    def __init__(self, data, offset, verbose=False):
        # Any container-specific data processing should happen before this 
        # function is called

        # For ease of identifying which image belongs to which addresses, map
        # them out now
        self._image_addrs = {}
        if self.images is not None:
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

    def __str__(self):
        return f'{self.offset:#x}: {self.hdr}'

    def export(self):
        # Just flatten all of the header/namedtuple types into dicts
        return _normalize_obj(self)
