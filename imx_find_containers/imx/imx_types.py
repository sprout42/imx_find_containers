import enum
from ..types import StructTupleMeta, ExportableIntEnum, ExportableIntFlag


class ContainerVersions(ExportableIntEnum):
    VERSION_0 = 0x00
    SRK_TABLE_VERSION = 0x42


class HeaderTag(ExportableIntEnum):
    DEK = 0x81
    CONTAINER = 0x87
    MESSAGE = 0x89
    SIGNATURE_BLOCK = 0x90
    CERTIFICATE = 0xAF
    SRK_TABLE = 0xD7
    SIGNATURE = 0xD8
    SRK = 0xE1


class SRKSet(ExportableIntEnum):
    NOAUTH = 0x00
    NXP = 0x01
    OEM = 0x02


class ImageType(ExportableIntEnum):
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


class CPUID(ExportableIntEnum):
    SC_R_A35_0 = 508
    SC_R_A53_0 = 1
    SC_R_A72_0 = 6
    SC_R_M4_0_PID0 = 278
    SC_R_M4_1_PID0 = 298


class MUID(ExportableIntEnum):
    SC_R_MU_0A = 213
    SC_R_M4_0_MU_1A = 297
    SC_R_M4_1_MU_1A = 317


class PartitionID(ExportableIntEnum):
    PARTITION_ID_M4 = 0
    PARTITION_ID_AP = 1


class HashType(ExportableIntEnum):
    SHA2_256 = 0x00
    SHA2_384 = 0x01
    SHA2_512 = 0x02


class CoreType(ExportableIntEnum):
    SC = 0x01
    CM4_0 = 0x02
    CM4_1 = 0x03
    A53 = 0x04
    A72 = 0x05
    SECO = 0x06
    V2X_P = 0x09
    V2X_S = 0x0A


class AlgType(ExportableIntEnum):
    RSA = 0x21
    ECDSA = 0x27


class ECDSACurve(ExportableIntEnum):
    PRIME256V1 = 0x01
    SEC348R1 = 0x02
    SEC521R1 = 0x03


class AESKeySize(ExportableIntEnum):
    AES128 = 0x10
    AES192 = 0x18
    AES256 = 0x20


class EncryptionAlg(ExportableIntEnum):
    AES = 0x55


class EncryptionMode(ExportableIntEnum):
    CBC = 0x66


class RSAKeySize(ExportableIntEnum):
    RSA2048 = 0x05
    RSA3072 = 0x06
    RSA4096 = 0x07


class CertPermissions(ExportableIntFlag):
    CONTAINER_SIGNING = 1 << 0
    SCU_DEBUG         = 1 << 1
    CM4_DEBUG         = 1 << 2
    APP_DEBUG         = 1 << 2  # Also VPU Debug
    FUSE_1            = 1 << 4  # SCU Version, Lifecycle
    FUSE_2            = 1 << 5  # Monotonic Counter


# NXP tools say that the max images per container should be 8
MAX_IMAGES_PER_CONTAINER = 8

# NXP docs say that two image containers should be no more than 8k, use 8k as 
# our sanity check header size
MAX_CONTAINER_SIZE = 8192


# All multi-byte fields are stored little-endian
class Header(metaclass=StructTupleMeta):
    fmt = '<BHB'
    fields = [
        'version', 'length', 'tag',
    ]


class ContainerHeader(metaclass=StructTupleMeta):
    fmt = '<BHBIHBBI'
    fields = [
        'version', 'length', 'tag', 'flags', 'sw_ver', 'fuse_ver', 'num_images', 'sig_offset',
    ]


class ImageHeader(metaclass=StructTupleMeta):
    fmt = '<IIQQII64s32s'
    fields = [
        'offset', 'size', 'dest', 'entry', 'flags', 'metadata', 'hash', 'iv',
    ]


class SignatureBlock(metaclass=StructTupleMeta):
    fmt = '<BHBHHHH'
    fields = [
        'version', 'length', 'tag', 'cert_offset', 'srk_table_offset', 'sig_offset', 'dek_offset',
    ]


class CertificateHeader(metaclass=StructTupleMeta):
    fmt = '<BHBHBB'
    fields = [
        'version', 'length', 'tag', 'sig_offset', 'perms_inv', 'perms',
    ]


class SignatureHeader(metaclass=StructTupleMeta):
    fmt = '<BHB4x'
    fields = [
        'version', 'length', 'tag',
    ]


class DEKHeader(metaclass=StructTupleMeta):
    fmt = '<BHBBBBB'
    fields = [
        'version', 'length', 'tag', 'flags', 'size', 'alg', 'mode',
    ]


class SRKTable(metaclass=StructTupleMeta):
    fmt = '<BHB'
    fields = [
        'tag', 'length', 'version',
    ]


class SRKRecordHeader(metaclass=StructTupleMeta):
    fmt = '<BHBBBBxHH'
    fields = [
        'tag', 'length', 'alg', 'hash', 'key_size', 'flags', 'mod_len', 'exp_len',
    ]


__all__ = [
    'ContainerVersions',
    'HeaderTag',
    'SRKSet',
    'ImageType',
    'CPUID',
    'MUID',
    'PartitionID',
    'HashType',
    'CoreType',
    'AlgType',
    'ECDSACurve',
    'AESKeySize',
    'EncryptionAlg',
    'EncryptionMode',
    'RSAKeySize',
    'CertPermissions',
    'MAX_IMAGES_PER_CONTAINER',
    'MAX_CONTAINER_SIZE',
    'Header',
    'ContainerHeader',
    'ImageHeader',
    'SignatureBlock',
    'CertificateHeader',
    'SignatureHeader',
    'DEKHeader',
    'SRKTable',
    'SRKRecordHeader',
]
