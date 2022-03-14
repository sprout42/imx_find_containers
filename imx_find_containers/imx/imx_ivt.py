from ..types import Container
from .. import utils
from .ivt_types import *


class iMXImageVectorTable(Container):
    @classmethod
    def is_container(cls, data, offset, verbose=False):
        if len(data) > offset + IVT_HEADER_SIZE:
            # use the raw byte values for the first level check to speed this up
            # Check for the IVT tag and a valid IVT version
            if data[offset] == IVTHeaderTag.IVT and \
                    data[offset+3] in (IVTHeaderVersion.IVT_VER_2, IVTHeaderVersion.IVT_VER_3):
                # Sanity check the header length and the contents of the
                # reserved fields in the IVT structure
                #
                # Only do a struct.unpack() instead of creating a full
                # StructTuple to save time. We don't need all of the header
                # elements for this check.
                _, length, _ = Header._struct.unpack_from(data, offset)
                _, reserved1, _, _, _, _, reserved2 = IVT._struct.unpack_from(data, offset + Header.size)

                # This might be an IVT, but first do a sanity check and make
                # sure the length, and reserved fields make sense.
                if len(data) >= offset + length and \
                        length == IVT_HEADER_SIZE and \
                        reserved1 == 0 and reserved2 == 0:
                    return True
                elif verbose:
                    # Probably not a container but print a message just in case
                    print(f'SKIP @ {offset:#x}: {data[offset:offset+IVT_HEADER_SIZE].hex()}')

        return False

    def init_from_data(self, data, offset):
        assert isinstance(data, bytes)
        self._parse_header(data, offset)

        # The boot_data, dcd, csf, and entry values are "absolute" addresses for
        # IVTs, but the "self" address is also the absolute value of the IVT
        # itself which means the relative offsets can be calculated based on the
        # offset of the IVT

        # Now parse the various IVT sections
        boot_data_offset = offset + (self.ivt.boot_data - self.ivt.addr)
        self._parse_boot_data(data, boot_data_offset)

        # DCD is optional
        if self.ivt.dcd != 0:
            dcd_offset = offset + (self.ivt.dcd - self.ivt.addr)
            self._parse_dcd(data, dcd_offset)

        # CSF is optional
        if self.ivt.csf != 0:
            csf_offset = offset + (self.ivt.csf - self.ivt.addr)
            self._parse_csf(data, csf_offset)

        # Now that CSF is parsed, identify the application data
        self.images = [self._parse_app(data)]

    def _parse_header(self, data, offset):
        assert len(data) > IVT_HEADER_SIZE
        if self._verbose:
            print(f'@ {offset:#x}: IVT HDR {data[offset:offset+IVT_HEADER_SIZE].hex()}')
        self.hdr = Header(data, offset)
        self.ivt = IVT(data, offset + Header.size)
        if self._verbose:
            print(self.hdr)
            print(self.ivt)

        assert self.hdr.tag == IVTHeaderTag.IVT
        assert self.hdr.version in (IVTHeaderVersion.IVT_VER_2, IVTHeaderVersion.IVT_VER_3)
        assert self.ivt.reserved1 == 0
        assert self.ivt.reserved2 == 0

        self.offset = offset
        self.end = offset + self.hdr.length

    def _parse_boot_data(self, data, offset):
        if self._verbose:
            print(f'@ {offset:#x}: BOOT DATA {data[offset:offset+BootData.size].hex()}')
        self.boot_data = BootData(data, offset)
        if self._verbose:
            print(self.boot_data)

    def _parse_dcd(self, data, offset):
        if self._verbose:
            print(f'@ {offset:#x}: DCD {data[offset:offset+DCD.size].hex()}')
        hdr = Header(data, offset)
        if self._verbose:
            print(hdr)

        assert hdr.tag == IVTHeaderTag.DCD
        assert hdr.version in IVTHeaderVersion.DCD_VER
        assert hdr.length <= MAX_DCD_SIZE

        cmd_offset = offset + Header.size
        cmd_end = cmd_offset + hdr.length
        cmd_range = range(cmd_offset, cmd_end)

        self.dcd = {
            'hdr': hdr,

            # The offset of the image data itself
            'offset': cmd_offset,
            'range': cmd_range,
            'cmds': [],
        }

        while cmd_offset in cmd_range:
            cmd = self._parse_cmd(data, cmd_offset)
            self.dcd['cmds'].append(cmd)
            cmd_offset += cmd['hdr'].length

    def _parse_cmd(self, data, offset):
        if self._verbose:
            print(f'@ {offset:#x}: CMD {data[offset:offset+Header.size].hex()}')
        hdr = Header(data, offset)
        if self._verbose:
            print(hdr)

        cmd = {
            'hdr': hdr,

            # The offset of the image data itself
            'offset': cmd_offset,
            'range': cmd_range,
        }

        #if hdr.tag ==


    def _parse_csf(self, data, offset):
        if self._verbose:
            print(f'@ {offset:#x}: CSF {data[offset:offset+CSF.size].hex()}')
        hdr = CSF(data, offset)
        if self._verbose:
            print(hdr)

    def _parse_app(self, data):
        # The application image itself should be included in the IVT length, but
        # unlike the i.MX Container "images" IVT application images don't appear
        # to have any header structures
        app_offset = offset + (self.hdr.entry - self.hdr.addr)

        if self.hdr.csf:
            # The CSF exists so use the CSF start address as the end of the
            # application
            app_end = self.hdr.csf
        else:
            # The IVT header length doesn't appear to indicate the actual size
            # of the IVT information itself OR the application length. The
            # BOOT_DATA start and length appear to encompass the entire size of
            # the boot information itself, so if there is no csf then use the
            # boot_data.length to determine the end address of the application

            # BOOT_DATA start most likely comes before the IVT header itself
            app_end = offset + self.boot_data.length - (self.hdr.addr - self.boot_data.start)

        app_len = app_end - app_offset
        if self._verbose:
            print(f'@ {app_offset:#x}: APPLICATION ({app_len:x}) {data[offset:offset+16].hex()}')

        # For some reason the BOOT_DATA.length sometimes exceeds the available
        # data
        if app_end > len(data):
            print(f'WARNING: (@ {app_offset:#x}) Application length exceeds available data: {len(data):#x} ! >= {app_end:#x}')
            app_end = len(data)

        app = {
            'offset': app_offset,
            'range': range(app_offset, app_end),
            'data': data[app_offset:app_end],
        }

        return app

__all__ = [
    'iMXImageVectorTable',
]
