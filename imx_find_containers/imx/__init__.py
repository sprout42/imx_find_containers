
from ..types import ContainerABC
from .. import utils
from .imx_types import *

class iMXImageContainer(ContainerABC):
    @classmethod
    def is_container(cls, data, offset, verbose=False):
        if len(data[offset:]) > ContainerHeader.size:
            #hdr = ContainerHeader.unpack_from(data, offset)
            #if hdr.version == ContanerVersions.VERSION_0 and \
            #        hdr.tag in (HeaderTag.CONTAINER, HeaderTag.MESSAGE):

            # use the raw byte values for the first level check to speed this up
            if data[offset] == ContanerVersions.VERSION_0 and \
                    data[offset + 3] in (HeaderTag.CONTAINER, HeaderTag.MESSAGE):
                # Only do a struct.unpack() instead of creating a full 
                # StructTuple to save time. We don't need all of the header 
                # elements for this check.
                elems = ContainerHeader._struct.unpack_from(data, offset)
                _, length, _, _, _, _, num_images, sig_offset = elems

                # This probably is a container, but first do a sanity check and 
                # make sure the length, number of images, or signature block 
                # offsets aren't too silly
                #if hdr.length <= MAX_CONTAINER_SIZE and \
                #        offset + hdr.length <= len(data) and \
                #        hdr.num_images <= MAX_IMAGES_PER_CONTAINER and \
                #        offset + hdr.sig_offset <= len(data) and \
                #        (hdr.num_images or hdr.sig_offset):
                #    return True

                if length <= MAX_CONTAINER_SIZE and \
                        offset + length <= len(data) and \
                        num_images <= MAX_IMAGES_PER_CONTAINER and \
                        offset + sig_offset <= len(data) and \
                        (num_images or sig_offset):
                    return True
                elif verbose:
                    # Probably not a container but print a message just in case
                    print(f'SKIP @ {offset:#x}: {data[offset:offset + ContainerHeader.size].hex()}')

        return False

    def __init__(self, data, offset, verbose=False):
        self._verbose = verbose

        assert isinstance(data, bytes)
        self._parse_header(data, offset)

        self.sigblock = None
        self.images = None

        if self.hdr.sig_offset:
            self._parse_sig_block(data, offset + self.hdr.sig_offset)

        # Only containers should have images
        if self.hdr.tag == HeaderTag.MESSAGE:
            assert not self.hdr.num_images

        if self.hdr.num_images:
            self.images = []
            start = offset + ContainerHeader.size
            step = ImageHeader.size
            stop = start + (step * self.hdr.num_images)

            for i in range(start, stop, step):
                self.images.append(self._parse_image(data, i))

        # Now do any standard container init
        super().__init__(data=data, offset=offset, verbose=verbose)

    def _parse_header(self, data, offset):
        assert len(data) > ContainerHeader.size
        if self._verbose:
            print(f'@ {offset:#x}: HDR {data[offset:offset+16].hex()}')
        self.hdr = ContainerHeader.unpack_from(data, offset)
        if self._verbose:
            print(self.hdr)

        assert self.hdr.version == ContanerVersions.VERSION_0
        assert self.hdr.tag in (HeaderTag.CONTAINER, HeaderTag.MESSAGE)

        self.offset = offset
        self.srk = {
            'set': utils.enum_or_int(SRKSet, self.hdr.flags & 0x00000003),
            'index': (self.hdr.flags & 0x00000030) >> 2,
            'revoke_mask': (self.hdr.flags & 0x00000F00) >> 8,
        }

        self.end = offset + self.hdr.length

    def _parse_image(self, data, offset):
        if self._verbose:
            print(f'@ {offset:#x}: IMG {data[offset:offset+16].hex()}')
        hdr = ImageHeader.unpack_from(data, offset)
        if self._verbose:
            print(hdr)

        img = {
            'hdr': hdr,

            # The offset of the image data itself
            'offset': None,
            'range': None,

            # Flags
            'type': utils.enum_or_int(ImageType, hdr.flags & 0x0000000F),
            'core_id': utils.enum_or_int(CoreType, (hdr.flags & 0x000000F0) >> 4),
            'hash_type': utils.enum_or_int(HashType, (hdr.flags & 0x00000700) >> 8),
            'encrypted': bool(hdr.flags & 0x00000800),
            'boot_flags': (hdr.flags & 0xFFFF0000) >> 16,

            # Image Metadata
            'cpu_id': utils.enum_or_int(CPUID, hdr.metadata & 0x000003FF),
            'mu_id': utils.enum_or_int(MUID, (hdr.metadata & 0x000FFC00) >> 10),
            'partition_id': utils.enum_or_int(PartitionID, (hdr.metadata & 0x0FF00000) >> 20),
            'data': None,
        }

        if hdr.offset:
            img['offset'] = self.offset + hdr.offset

            if hdr.size:
                # Ensure that the container data is large enough to hold this 
                # image.  The image offsets are offsets from the start of the 
                # container header, unlike other sections in the container.
                end = img['offset'] + hdr.size

                if len(data) < end:
                    print(f'WARNING: (@ {offset:#x}) Image length invalid: {len(data):#x} ! >= {end:#x}')
                else:
                    img['range'] = range(img['offset'], end)
                    img['data'] = data[img['offset']:end]

            elif img['type'] == ImageType.DCD_DDR:
                # The DDR initialization image is embedded in the SCFW image, 
                # but there is a dummy image header with a 0 size, if that is 
                # the case for this image don't print a warning.
                pass

            else:
                print(f'WARNING: (@ {offset:#x}) empty image: offset = {hdr.offset}, size = {hdr.size}')
        else:
            print(f'WARNING: (@ {offset:#x}) empty image: offset = {hdr.offset}, size = {hdr.size}')

        return img

    def _parse_sig_block(self, data, offset):
        if self._verbose:
            print(f'@ {offset:#x}: BLK {data[offset:offset+16].hex()}')
        hdr = SignatureBlock.unpack_from(data, offset)
        if self._verbose:
            print(hdr)

        assert hdr.version == ContanerVersions.VERSION_0
        assert hdr.tag == HeaderTag.SIGNATURE_BLOCK

        self.sigblock = {
            'hdr': hdr,
            'offset': offset,
            'srk_table': self._parse_srk_table(data, offset + hdr.srk_table_offset),
            'sig': self._parse_sig(data, offset + hdr.sig_offset),
            'cert': None,
            'dek': None,
        }

        if hdr.cert_offset != 0:
            self.sigblock['cert'] = self._parse_cert(data, offset + hdr.cert_offset)

        if hdr.dek_offset != 0:
            self.sigblock['dek'] = self._parse_dek(data, offset + hdr.dek_offset)

    def _parse_srk_table(self, data, offset):
        if self._verbose:
            print(f'@ {offset:#x}: TBL {data[offset:offset+16].hex()}')
        hdr = SRKTable.unpack_from(data, offset)
        if self._verbose:
            print(hdr)

        assert hdr.version == ContanerVersions.SRK_TABLE_VERSION
        assert hdr.tag == HeaderTag.SRK_TABLE

        table = {
            'hdr': hdr,
            'offset': offset,
            'records': [],
        }

        srk_offset = offset + SRKTable.size
        # There are always 4 keys
        for i in range(4):
            srk = self._parse_srk(data, srk_offset)
            table['records'].append(srk)
            srk_offset += srk['hdr'].length

        assert srk_offset == offset + hdr.length

        return table

    def _parse_srk(self, data, offset):
        if self._verbose:
            print(f'@ {offset:#x}: SRK {data[offset:offset+16].hex()}')
        hdr = SRKRecordHeader.unpack_from(data, offset)
        if self._verbose:
            print(hdr)

        assert hdr.tag == HeaderTag.SRK

        record = {
            'hdr': hdr,
            'offset': offset,
            'type': AlgType(hdr.alg),
            'hash': HashType(hdr.hash),
        }

        if record['type'] == AlgType.RSA:
            record['key_size'] = RSAKeySize(hdr.key_size)

            mod_offset = offset + SRKRecordHeader.size
            exp_offset = mod_offset + hdr.mod_len
            end = exp_offset + hdr.exp_len
            record['modulus'] = data[mod_offset:exp_offset]
            record['exponent'] = data[exp_offset:end]

        else:
            # The ECDSA key info uses the same fields as the RSA key, but the 
            # fields mean different things
            record['curve'] = ECDSACurve(hdr.key_size)

            x_offset = offset + SRKRecordHeader.size
            y_offset = x_offset + hdr.mod_len
            end = y_offset + hdr.exp_len
            record['x'] = data[x_offset:y_offset]
            record['y'] = data[y_offset:end]

        assert hdr.length == end - offset

        return record

    def _parse_sig(self, data, offset):
        if self._verbose:
            print(f'@ {offset:#x}: SIG {data[offset:offset+16].hex()}')
        hdr = SignatureHeader.unpack_from(data, offset)
        if self._verbose:
            print(hdr)

        assert hdr.version == ContanerVersions.VERSION_0
        assert hdr.tag == HeaderTag.SIGNATURE

        sig = {
            'hdr': hdr,
            'offset': offset,
        }

        sig_offset = offset + SignatureHeader.size
        end = offset + hdr.length
        sig['data'] = data[sig_offset:end]

        return sig

    def _parse_cert(self, data, offset):
        if self._verbose:
            print(f'@ {offset:#x}: CRT {data[offset:offset+16].hex()}')
        hdr = CertificateHeader.unpack_from(data, offset)
        if self._verbose:
            print(hdr)

        assert hdr.version == ContanerVersions.VERSION_0
        assert hdr.tag == HeaderTag.CERTIFICATE
        assert utils.invert(hdr.perms) == hdr.perms_inv

        cert = {
            'hdr': hdr,
            'offset': offset,
            'perm': CertPermissions(hdr.perms),
        }

        # The public key in the cert uses the same format as the SRK records 
        # used in the SRKTable
        cert['pub'] = self._parse_srk(data, offset + CertificateHeader.size)

        sig_offset = offset + hdr.sig_offset
        end = offset + hdr.length
        cert['sig'] = data[sig_offset:end]

        return cert

    def _parse_dek(self, data, offset):
        if self._verbose:
            print(f'@ {offset:#x}: DEK {data[offset:offset+16].hex()}')
        hdr = DEKHeader.unpack_from(data, offset)
        if self._verbose:
            print(hdr)

        assert hdr.version == ContanerVersions.VERSION_0
        assert hdr.tag == HeaderTag.DEK

        assert hdr.alg == EncryptionAlg.AES
        assert hdr.mode == EncryptionMode.CBC

        dek = {
            'hdr': hdr,
            'offset': offset,
            'kek': bool(hdr.flags & 0x80),
            'key_size': utils.enum_or_int(AESKeySize, hdr.size),
        }

        key_offset = offset + DEKHeader.size
        end = offset + hdr.length
        dek['key'] = data[key_offset:end]

        return dek
