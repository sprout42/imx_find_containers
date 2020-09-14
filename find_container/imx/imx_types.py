import enum

from ..types import StructTuple


class ContanerVersions(enum.IntEnum):
    VERSION_0 = 0x00
    SRK_TABLE_VERSION = 0x42

    @classmethod
    def to_yaml(cls, representer, node):
        enum_str = f'{__class__.__name__}.{node.name} ({node.value:#x})'
        return representer.represent_scalar('!enum.IntEnum', enum_str)


class HeaderTag(enum.IntEnum):
    DEK = 0x81
    CONTAINER = 0x87
    MESSAGE = 0x89
    SIGNATURE_BLOCK = 0x90
    CERTIFICATE = 0xAF
    SRK_TABLE = 0xD7
    SIGNATURE = 0xD8
    SRK = 0xE1

    @classmethod
    def to_yaml(cls, representer, node):
        enum_str = f'{__class__.__name__}.{node.name} ({node.value:#x})'
        return representer.represent_scalar('!enum.IntEnum', enum_str)


class SRKSet(enum.IntEnum):
    NOAUTH = 0x00
    NXP = 0x01
    OEM = 0x02

    @classmethod
    def to_yaml(cls, representer, node):
        enum_str = f'{__class__.__name__}.{node.name} ({node.value:#x})'
        return representer.represent_scalar('!enum.IntEnum', enum_str)


class ImageType(enum.IntEnum):
    CSF = 0x01
    SCD = 0x02
    EXE = 0x03
    DATA = 0x04
    DCD_DDR = 0x05
    SECO = 0x06
    PROVISIONING = 0x07
    DEK = 0x08
    V2X_PRIMARY = 0x0B
    V2X_SECONDARY = 0x0C
    V2X_ROM = 0x0D
    V2X_DUMMY = 0x0E

    @classmethod
    def to_yaml(cls, representer, node):
        enum_str = f'{__class__.__name__}.{node.name} ({node.value:#x})'
        return representer.represent_scalar('!enum.IntEnum', enum_str)


class CPUID(enum.IntEnum):
    SC_R_A35_0 = 508
    SC_R_A53_0 = 1
    SC_R_A72_0 = 6
    SC_R_M4_0_PID0 = 278
    SC_R_M4_1_PID0 = 298

    @classmethod
    def to_yaml(cls, representer, node):
        enum_str = f'{__class__.__name__}.{node.name} ({node.value:#x})'
        return representer.represent_scalar('!enum.IntEnum', enum_str)


class MUID(enum.IntEnum):
    SC_R_MU_0A = 213
    SC_R_M4_0_MU_1A = 297
    SC_R_M4_1_MU_1A = 317

    @classmethod
    def to_yaml(cls, representer, node):
        enum_str = f'{__class__.__name__}.{node.name} ({node.value:#x})'
        return representer.represent_scalar('!enum.IntEnum', enum_str)


class PartitionID(enum.IntEnum):
    PARTITION_ID_M4 = 0
    PARTITION_ID_AP = 1

    @classmethod
    def to_yaml(cls, representer, node):
        enum_str = f'{__class__.__name__}.{node.name} ({node.value:#x})'
        return representer.represent_scalar('!enum.IntEnum', enum_str)


class HashType(enum.IntEnum):
    SHA2_256 = 0x00
    SHA2_384 = 0x01
    SHA2_512 = 0x02

    @classmethod
    def to_yaml(cls, representer, node):
        enum_str = f'{__class__.__name__}.{node.name} ({node.value:#x})'
        return representer.represent_scalar('!enum.IntEnum', enum_str)


class CoreType(enum.IntEnum):
    SC = 0x01
    CM4_0 = 0x02
    CM4_1 = 0x03
    A53 = 0x04
    A72 = 0x05
    SECO = 0x06
    V2X_P = 0x09
    V2X_S = 0x0A

    @classmethod
    def to_yaml(cls, representer, node):
        enum_str = f'{__class__.__name__}.{node.name} ({node.value:#x})'
        return representer.represent_scalar('!enum.IntEnum', enum_str)


class AlgType(enum.IntEnum):
    RSA = 0x21
    ECDSA = 0x27

    @classmethod
    def to_yaml(cls, representer, node):
        enum_str = f'{__class__.__name__}.{node.name} ({node.value:#x})'
        return representer.represent_scalar('!enum.IntEnum', enum_str)


class ECDSACurve(enum.IntEnum):
    PRIME256V1 = 0x01
    SEC348R1 = 0x02
    SEC521R1 = 0x03

    @classmethod
    def to_yaml(cls, representer, node):
        enum_str = f'{__class__.__name__}.{node.name} ({node.value:#x})'
        return representer.represent_scalar('!enum.IntEnum', enum_str)


class AESKeySize(enum.IntEnum):
    AES128 = 0x10
    AES192 = 0x18
    AES256 = 0x20

    @classmethod
    def to_yaml(cls, representer, node):
        enum_str = f'{__class__.__name__}.{node.name} ({node.value:#x})'
        return representer.represent_scalar('!enum.IntEnum', enum_str)


class EncryptionAlg(enum.IntEnum):
    AES = 0x55

    @classmethod
    def to_yaml(cls, representer, node):
        enum_str = f'{__class__.__name__}.{node.name} ({node.value:#x})'
        return representer.represent_scalar('!enum.IntEnum', enum_str)


class EncryptionMode(enum.IntEnum):
    CBC = 0x66

    @classmethod
    def to_yaml(cls, representer, node):
        enum_str = f'{__class__.__name__}.{node.name} ({node.value:#x})'
        return representer.represent_scalar('!enum.IntEnum', enum_str)


class RSAKeySize(enum.IntEnum):
    RSA2048 = 0x05
    RSA3072 = 0x06
    RSA4096 = 0x07

    @classmethod
    def to_yaml(cls, representer, node):
        enum_str = f'{__class__.__name__}.{node.name} ({node.value:#x})'
        return representer.represent_scalar('!enum.IntEnum', enum_str)


class CertPermissions(enum.IntFlag):
    CONTAINER_SIGNING = 1 << 0
    SCU_DEBUG         = 1 << 1
    CM4_DEBUG         = 1 << 2
    APP_DEBUG         = 1 << 2  # Also VPU Debug
    FUSE_1            = 1 << 4  # SCU Version, Lifecycle
    FUSE_2            = 1 << 5  # Monotonic Counter

    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_scalar('!enum.IntFlag', repr(node))


# NXP tools say that the max images per container should be 8
MAX_IMAGES_PER_CONTAINER = 8

# NXP docs say that two image containers should be no more than 8k, use 8k as 
# our sanity check header size
MAX_CONTAINER_SIZE = 8192


# All multi-byte fields are stored little-endian
Header = StructTuple('Header', '<BHB', [
    'version', 'length', 'tag',
])


ContainerHeader = StructTuple('ContainerHeader', '<BHBIHBBI', [
    'version', 'length', 'tag', 'flags', 'sw_ver', 'fuse_ver', 'num_images', 'sig_offset',
])


ImageHeader = StructTuple('ImageHeader', '<IIQQII64s32s', [
    'offset', 'size', 'dest', 'entry', 'flags', 'metadata', 'hash', 'iv',
])


SignatureBlock = StructTuple('SignatureBlock', '<BHBHHHH', [
    'version', 'length', 'tag', 'cert_offset', 'srk_table_offset', 'sig_offset', 'dek_offset',
])


CertificateHeader = StructTuple('CertificateHeader', '<BHBHBB', [
    'version', 'length', 'tag', 'sig_offset', 'perms_inv', 'perms',
])


SignatureHeader = StructTuple('SignatureHeader', '<BHB4x', [
    'version', 'length', 'tag',
])


DEKHeader = StructTuple('DEKHeader', '<BHBBBBB', [
    'version', 'length', 'tag', 'flags', 'size', 'alg', 'mode',
])


SRKTable = StructTuple('SRKTable', '<BHB', [
    'tag', 'length', 'version',
])


SRKRecordHeader = StructTuple('SRKRecordHeader', '<BHBBBBxHH', [
    'tag', 'length', 'alg', 'hash', 'key_size', 'flags', 'mod_len', 'exp_len',
])
