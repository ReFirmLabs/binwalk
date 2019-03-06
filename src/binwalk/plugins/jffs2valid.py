import struct
import binascii
import binwalk.core.plugin


class JFFS2ValidPlugin(binwalk.core.plugin.Plugin):

    '''
    Helps validate JFFS2 signature results.

    The JFFS2 signature rules catch obvious cases, but inadvertently
    mark some valid JFFS2 nodes as invalid due to  padding (0xFF's or
    0x00's) in between nodes.
    '''
    MODULES = ['Signature']

    def _check_crc(self, node_header):
        # struct and binascii want a bytes object in Python3
        node_header = binwalk.core.compat.str2bytes(node_header)

        # Get the header's reported CRC value
        if node_header[0:2] == b"\x19\x85":
            header_crc = struct.unpack(">I", node_header[8:12])[0]
        else:
            header_crc = struct.unpack("<I", node_header[8:12])[0]

        # Calculate the actual CRC
        calculated_header_crc = (binascii.crc32(node_header[0:8], -1) ^ -1) & 0xffffffff

        # Make sure they match
        return (header_crc == calculated_header_crc)

    def scan(self, result):
        if result.file and result.description.lower().startswith('jffs2 filesystem'):

            # Seek to and read the suspected JFFS2 node header
            fd = self.module.config.open_file(result.file.path, offset=result.offset)
            # JFFS2 headers are only 12 bytes in size, but reading larger amounts of
            # data from disk speeds up repeated disk access and decreases performance
            # hits (disk caching?).
            #
            # TODO: Should this plugin validate the *entire* JFFS2 file system, rather
            # than letting the signature module find every single JFFS2 node?
            node_header = fd.read(1024)
            fd.close()

            result.valid = self._check_crc(node_header[0:12])
