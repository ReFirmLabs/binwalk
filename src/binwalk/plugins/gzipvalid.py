import binwalk.core.C
import binwalk.core.plugin
from binwalk.core.common import BlockFile

class GzipValidPlugin(binwalk.core.plugin.Plugin):
    '''
    Validates gzip compressed data. Almost identical to zlibvalid.py.
    '''
    MODULES = ['Signature']

    MIN_DECOMP_SIZE = 16 * 1024
    MAX_DATA_SIZE = 33 * 1024

    TINFL = "tinfl"
    TINFL_FUNCTIONS = [
        binwalk.core.C.Function(name="is_deflated", type=int),
    ]

    def init(self):
        # Load libtinfl.so
        self.tinfl = binwalk.core.C.Library(self.TINFL, self.TINFL_FUNCTIONS)

    def scan(self, result):
        # If this result is a gzip signature match, try to decompress the data
        if result.file and result.description.lower().startswith('gzip'):
            # Seek to and read the suspected gzip data
            fd = self.module.config.open_file(result.file.name, offset=result.offset, length=self.MAX_DATA_SIZE)
            data = fd.read(self.MAX_DATA_SIZE)
            fd.close()

            # Grab the flags and initialize the default offset of the start of
            # compressed data.
            flags = int(ord(data[3]))
            offset = 10

            # If there is a comment or the original file name, find the end of that
            # string and start decompression from there.
            if (flags & 0x0C) or (flags & 0x10):
                while data[offset] != "\x00":
                    offset += 1
                offset += 1

            # Check if this is valid deflate data (no zlib header)
            decomp_size = self.tinfl.is_deflated(data[offset:], len(data[offset:]), 0)
            if decomp_size <= 0:
                result.valid = False

