import zlib
import binwalk.core.compat
import binwalk.core.plugin
from binwalk.core.common import BlockFile


class GzipValidPlugin(binwalk.core.plugin.Plugin):

    '''
    Validates gzip compressed data. Almost identical to zlibvalid.py.
    '''
    MODULES = ['Signature']

    MAX_DATA_SIZE = 33 * 1024

    def scan(self, result):
        # If this result is a gzip signature match, try to decompress the data
        if result.file and result.description.lower().startswith('gzip'):
            # Seek to and read the suspected gzip data
            fd = self.module.config.open_file(result.file.path, offset=result.offset, length=self.MAX_DATA_SIZE)
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

            # Append basic zlib header to the beginning of the compressed data
            data = "\x78\x9C" + data[offset:]

            # Check if this is valid deflate data (no zlib header)
            try:
                zlib.decompress(binwalk.core.compat.str2bytes(data))
            except zlib.error as e:
                error = str(e)
                # Truncated input data results in error -5.
                # gzip uses different checksums than zlib, which results in
                # error -3.
                if not error.startswith("Error -5") and not error.startswith("Error -3"):
                    result.valid = False
