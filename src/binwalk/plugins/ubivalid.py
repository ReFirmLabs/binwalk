import struct
import binascii
import binwalk.core.plugin
import binwalk.core.compat
from collections import defaultdict

class UBIValidPlugin(binwalk.core.plugin.Plugin):
    '''
    Helps validate UBI erase count signature results.

    Checks header CRC and calculates jump value
    '''
    MODULES = ['Signature']

    def _check_crc(self, header):
        # Get the header's reported CRC value
        header_crc = struct.unpack(">I", header[60:64])[0]

        # Calculate the actual CRC
        calculated_header_crc = ~binascii.crc32(header[0:60]) & 0xffffffff

        # Make sure they match
        return header_crc == calculated_header_crc

    def _read_ec_header(self, result, offset):
        # Seek to and read the suspected UBI erase count header

        fd = self.module.config.open_file(result.file.name, offset=(result.offset + offset))
        ec_header = binwalk.core.compat.str2bytes(fd.read(64))
        fd.close()

        if ec_header:
            magic = ec_header[0:4]
            if self._check_crc(ec_header) and magic == b'UBI#':
                return ec_header

    def _read_vid_header(self, result, ec_header, offset):
        vid_hdr_offset = struct.unpack(">i", ec_header[16:20])[0]

        fd = self.module.config.open_file(result.file.name, offset=(result.offset + offset + vid_hdr_offset))
        vid_header = binwalk.core.compat.str2bytes(fd.read(64))
        fd.close()

        if vid_header:
            magic = vid_header[0:4]
            if self._check_crc(vid_header) and magic == b'UBI!':
                return vid_header

    def _check_blocksize(self, result):
        for blocksize in range(10,20):
            ec_header = self._read_ec_header(result, 1<<blocksize)
            if ec_header:
                return blocksize

    def scan(self, result):
        if not result.file or not result.description.lower().startswith('ubi erase count header'):
            return

        blocksize = self._check_blocksize(result)
        if not blocksize:
            return

        seen = defaultdict(lambda: defaultdict(int))
        count = 0

        while True:
            ec_header = self._read_ec_header(result, count * (1<<blocksize))
            if not ec_header:
                break

            vid_header = self._read_vid_header(result, ec_header, count * (1<<blocksize))

            if not vid_header:
                count += 1
                continue

            magic, version, vol_type, copy_flag, compat, vol_id, lnum, data_size, used_ebs, data_pad, data_crc, sqnum, crc = struct.unpack(">4s4BLL4x4L4xQ12xL",vid_header)

            if seen[vol_id][lnum]:
                break

            seen[vol_id][lnum] = 1
            count += 1

        if count == 0:
            return

        result.valid = True
        result.size = count * (1 << blocksize)
        result.jump = result.size
