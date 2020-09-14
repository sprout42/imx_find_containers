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
