
import io
import struct

from pyfdt.pyfdt import FdtBlobParse

from ..types import ContainerABC
from .. import utils

from .fit_types import *

class FITContainer(ContainerABC):
    @classmethod
    def is_container(cls, data, offset, verbose=False):
        # First 4 bytes will be the FDT_MAGIC of 0xD00DFEED
        # second 4 bytes is the size
        magic, size = struct.unpack_from('>II', data[offset:])
        return magic == 0xD00DFEED and len(data) >= size


    def __init__(self, data, offset, verbose=False):
        self._verbose = verbose
        self.offset = offset

        # It isn't strictly necessary to parse the header here since the pyfdt 
        # module will parse the entire FDT for us, but this will allow the scan 
        # results entry to be more meaningful
        self.hdr = FDTHeader.unpack_from(data, offset)

        self.end = offset + self.hdr.totalsize
        imgrange = range(offset, self.end)

        dtb = data[offset:self.end]
        parsed_dtb = FdtBlobParse(io.BytesIO(dtb))
        dts = parsed_dtb.to_fdt().to_dts()

        # Add the DTB and DTS contents as images with custom extensions to get 
        # exports of the files.
        self.images = [
            {'range': imgrange, 'fileext': f'dtb', 'data': dtb},
            {'range': imgrange, 'fileext': f'dts', 'data': dts},
        ]

        # Now do any standard container init
        super().__init__(data=data, offset=offset, verbose=verbose)


    def fix_offset(self, offset):
        # FIT images can be in other images, so this function allows correcting 
        # the offsets so they are correct according to the top-level file 
        # instead of the file they were extracted from.
        self.offset = offset
        self.end = offset + self.hdr.totalsize

        # First image is the DTB
        self.images[0]['range'] = range(offset, self.end)

        # Second image is the DTS
        self.images[1]['range'] = range(offset, self.end)
