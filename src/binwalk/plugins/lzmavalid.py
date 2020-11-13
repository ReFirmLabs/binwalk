import binwalk.core.plugin
import binwalk.core.compat
from binwalk.core.common import BlockFile


class LZMAPlugin(binwalk.core.plugin.Plugin):

    '''
    Validates lzma signature results.
    '''
    MODULES = ['Signature']

    # Some lzma files exclude the file size, so we have to put it back in.
    # See also the lzmamod.py plugin.
    FAKE_LZMA_SIZE = "\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF"

    # Check up to the first 64KB
    MAX_DATA_SIZE = 64 * 1024

    def init(self):
        try:
            try:
                import lzma
            except ImportError:
                from backports import lzma
            self.decompressor = lzma.decompress
        except ImportError as e:
            self.decompressor = None

    def is_valid_lzma(self, data):
        valid = True

        if self.decompressor is not None:
            # The only acceptable exceptions are those indicating that the
            # input data was truncated.
            try:
                self.decompressor(binwalk.core.compat.str2bytes(data))
            except IOError as e:
                # The Python2 module gives this error on truncated input data.
                if str(e) != "unknown BUF error":
                    valid = False
            except Exception as e:
                # The Python3 module gives this error on truncated input data.
                # The inconsistency between modules is a bit worrisome.
                if str(e) != "Compressed data ended before the end-of-stream marker was reached":
                    valid = False

        return valid

    def scan(self, result):
        # If this result is an lzma signature match, try to decompress the data
        if result.valid and result.file and result.description.lower().startswith('lzma compressed data'):

            # Seek to and read the suspected lzma data
            fd = self.module.config.open_file(result.file.path, offset=result.offset, length=self.MAX_DATA_SIZE)
            data = fd.read(self.MAX_DATA_SIZE)
            fd.close()

            # Validate the original data; if that fails, maybe it is missing the size field,
            # so try again with a dummy size field in place.
            if not self.is_valid_lzma(data):
                data = data[:5] + self.FAKE_LZMA_SIZE + data[5:]
                if not self.is_valid_lzma(data):
                    result.valid = False
                else:
                    result.description = ",".join(result.description.split(',')[:-1] + [" missing uncompressed size"])
