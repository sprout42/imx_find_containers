from ..types import StructTupleMeta, ExportableIntEnum, ExportableIntFlag


class IVTHeaderVersion(ExportableIntEnum):
    IVT_VER_2 = 0x40
    IVT_VER_3 = 0x41
    DCD_VER   = 0x41

class IVTHeaderTag(ExportableIntEnum):
    IVT = 0xD1
    DCD = 0xD2
    WRITE_DATA = 0xCC
    CHECK_DATA = 0xCF
    NOP = 0xC0
    UNLOCK = 0xB2


IVT_HEADER_SIZE = 32
MAX_DCD_SIZE = 1768


# All multi-byte fields in these various headers are in little-endian format
# EXCEPT
# for some bizarre reason the length fields are in big-endian?
# Because of this all structures are broken up into the common header field (in
# big-endian) and any "other" data is in a seperate structure
class Header(metaclass=StructTupleMeta):
    fmt = '>BHB'
    fields = [
        'tag', 'length', 'version',
    ]


class IVT(metaclass=StructTupleMeta):
    fmt = '>IIIIIII'
    fields = [
        'entry', 'reserved1', 'dcd', 'boot_data', 'addr', 'csf', 'reserved2',
    ]


class BootData(metaclass=StructTupleMeta):
    fmt = '>III'
    fields = [
        'start', 'length', 'plugins',
    ]


__all__ = [
    'IVTHeaderVersion',
    'IVTHeaderTag',
    'IVT_HEADER_SIZE',
    'MAX_DCD_SIZE',
    'Header',
    'IVT',
    'BootData',
]
