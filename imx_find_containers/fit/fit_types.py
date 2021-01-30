from ..types import StructTupleMeta


# FDT fields are big-endian
class FDTHeader(metaclass=StructTupleMeta):
    fmt = '>IIIIIII'
    fields = [
        'magic', 'totalsize', 'off_dt_struct', 'off_dt_strings', 'off_mem_rsvmap', 'version', 'last_comp_version',
    ]


__all__ = [
    'FDTHeader',
]
