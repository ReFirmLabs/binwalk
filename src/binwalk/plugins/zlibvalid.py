import binwalk.core.C
import binwalk.core.plugin
from binwalk.core.common import BlockFile

class ZlibPlugin(binwalk.core.plugin.Plugin):
    '''
    Searches for and validates zlib compressed data.
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
        # If this result is a zlib signature match, try to decompress the data
        if result.file and result.description.lower().startswith('zlib'):
            # Seek to and read the suspected zlib data
            fd = self.module.config.open_file(result.file.name, offset=result.offset, length=self.MAX_DATA_SIZE)
            data = fd.read(self.MAX_DATA_SIZE)
            fd.close()

            # Check if this is valid zlib data
            decomp_size = self.tinfl.is_deflated(data, len(data), 1)
            if decomp_size > 0:
                result.description += ", uncompressed size >= %d" % decomp_size
            else:
                result.valid = False

