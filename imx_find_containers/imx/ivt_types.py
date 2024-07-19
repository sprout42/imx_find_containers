from ..types import StructTupleMeta, ExportableIntEnum, ExportableIntFlag


class IVTHeaderVersion(ExportableIntEnum):
    IVT_VER_2 = 0x40
    IVT_VER_3 = 0x41

class DCDHeaderVersion(ExportableIntEnum):
    DCD_VER_0 = 0x40
    DCD_VER_1 = 0x41

class IVTHeaderTag(ExportableIntEnum):
    IVT = 0xD1
    DCD = 0xD2
    CSF = 0xD4
    CRT = 0xD7
    SIG = 0xD8
    MAC = 0xAC

class DCDCommand(ExportableIntEnum):
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
    fmt = '<IIIIIII'
    fields = [
        'entry', 'reserved1', 'dcd', 'boot_data', 'addr', 'csf', 'reserved2',
    ]


class BootData(metaclass=StructTupleMeta):
    fmt = '<III'
    fields = [
        'start', 'length', 'plugins',
    ]


# DCD commands are big-endian


class DCDWriteCommand(metaclass=StructTupleMeta):
    fmt = '>II'
    fields = [
        'address', 'value',
    ]


class DCDCheckCommand(metaclass=StructTupleMeta):
    fmt = '>III'
    fields = [
        'address', 'mask', 'count',
    ]


class DCDUnlockCommand(metaclass=StructTupleMeta):
    fmt = '>I'
    fields = [
        'value',
    ]


DCD_COMMAND_TO_STRUCT = {
    DCDCommand.WRITE_DATA: DCDWriteCommand,
    DCDCommand.CHECK_DATA: DCDCheckCommand,
    DCDCommand.UNLOCK: DCDUnlockCommand,
}


__all__ = [
    'IVTHeaderVersion',
    'DCDHeaderVersion',
    'IVTHeaderTag',
    'DCDCommand',
    'IVT_HEADER_SIZE',
    'MAX_DCD_SIZE',
    'Header',
    'IVT',
    'BootData',
    'DCDWriteCommand',
    'DCDCheckCommand',
    'DCDUnlockCommand',
    'DCD_COMMAND_TO_STRUCT',
]
