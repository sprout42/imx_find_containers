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
            self.dcd = self._parse_dcd(data, dcd_offset)
        else:
            self.dcd = None

        # CSF is optional
        if self.ivt.csf != 0:
            csf_offset = offset + (self.ivt.csf - self.ivt.addr)
            self.csf = self._parse_csf(data, csf_offset)
        else:
            self.csf = None

        # Now that CSF is parsed, identify the application data, in theory this 
        # can be a list of multiple images but the iMX6 structures only support 
        # one. The correct application offset will be identified in the 
        # _parse_app function.
        self.images = [self._parse_app(data, offset)]

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
        assert self.hdr.version in list(IVTHeaderVersion)
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
            print(f'@ {offset:#x}: DCD {data[offset:offset+Header.size].hex()}')
        hdr = Header(data, offset)
        if self._verbose:
            print(hdr)

        assert hdr.tag == IVTHeaderTag.DCD
        assert hdr.version in list(DCDHeaderVersion)
        assert hdr.length <= MAX_DCD_SIZE

        cmds_start = offset + hdr.size
        cmds_end = offset + hdr.length

        dcd = {
            'hdr': hdr,
            'offset': offset,
            'range': range(cmds_start, cmds_end),
            'cmds': [],
        }

        offset = cmds_start
        while offset < cmds_end:
            cmd = self._parse_dcd_cmd(data, offset)
            dcd['cmds'].append(cmd)
            offset += cmd['hdr'].length

        return dcd

    def _parse_dcd_cmd(self, data, offset):
        if self._verbose:
            print(f'@ {offset:#x}: CMD {data[offset:offset+Header.size].hex()}')
        hdr = Header(data, offset)
        if self._verbose:
            print(hdr)

        assert hdr.tag in list(DCDCommand)

        cmd = {
            'hdr': hdr,
            'offset': offset,
            'range': range(offset+Header.size, offset+hdr.length),
            'commands': None,
        }

        # For every command except "NOP" parse the specified number of command 
        # data structures based on the length
        cmd_struct = DCD_COMMAND_TO_STRUCT[hdr.tag]
        cmd_range = range(offset+hdr.size, offset+hdr.length, cmd_struct.size)
        cmd['commands'] = [cmd_struct(data, off) for off in cmd_range]

        return cmd

    def _parse_csf(self, data, offset):
        if self._verbose:
            #print(f'@ {offset:#x}: CSF {data[offset:offset+CSF.size].hex()}')
            print(f'@ {offset:#x}: CSF {data[offset:offset+Header.size].hex()}')
        #hdr = CSF(data, offset)
        hdr = Header(data, offset)
        if self._verbose:
            print(hdr)

        csf = {
            'hdr': hdr,
            'offset': offset,
            'range': range(offset+Header.size, offset+hdr.length),
        }

        return csf

    def _parse_app(self, data, offset):
        # The application image itself should be included in the IVT length, but
        # unlike the i.MX Container "images" IVT application images don't appear
        # to have any header structures
        app_start = offset + (self.boot_data.start - self.ivt.addr)
        app_end = app_start + self.boot_data.length

        # Adjust the application entry point
        app_entry = offset + (self.ivt.entry - self.ivt.addr)

        if self._verbose:
            print(f'@ {app_start:#x}: APP ({self.boot_data.length:#x} bytes) ENTRY @ {app_entry:#x}: {data[app_entry:app_entry+16].hex(" ", 4)}...')

        # For some reason the BOOT_DATA.length sometimes exceeds the available
        # data
        if app_end > len(data):
            print(f'WARNING: (@ {app_start:#x}) Application length exceeds available data: {len(data):#x} ! >= {app_end:#x}')
            app_end = len(data)

        app = {
            'offset': app_start,
            'entry': app_entry,
            'range': range(app_start, app_end),
            'data': data[app_start:app_end],
        }

        return app


__all__ = [
    'iMXImageVectorTable',
]
