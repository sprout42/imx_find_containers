
from ..types import StructTuple


# FDT fields are big-endian
FDTHeader = StructTuple('FDTHeader', '>IIIIIII', [
    'magic', 'totalsize', 'off_dt_struct', 'off_dt_strings', 'off_mem_rsvmap', 'version', 'last_comp_version',
])
