import time
import math
import binwalk.core.plugin


class TarPlugin(binwalk.core.plugin.Plugin):

    MODULES = ['Signature']

    # "borrowed from pythons tarfile module"
    TAR_BLOCKSIZE = 512

    def nts(self, s):
        """
        Convert a null-terminated string field to a python string.
        """
        # Use the string up to the first null char.
        p = s.find("\0")
        if p == -1:
            return s
        return s[:p]

    def nti(self, s):
        """
        Convert a number field to a python number.
        """
        # There are two possible encodings for a number field, see
        # itn() below.
        if s[0] != chr(0x80):
            try:
                n = int(self.nts(s) or "0", 8)
            except ValueError:
                raise ValueError("invalid tar header")
        else:
            n = 0
            for i in xrange(len(s) - 1):
                n <<= 8
                n += ord(s[i + 1])
        return n

    def scan(self, result):
        if result.description.lower().startswith('posix tar archive'):
            is_tar = True
            file_offset = result.offset
            fd = self.module.config.open_file(result.file.path, offset=result.offset)

            while is_tar:
                # read in the tar header struct
                buf = fd.read(self.TAR_BLOCKSIZE)

                # check to see if we are still in a tarball
                if buf[257:262] == 'ustar':
                    # get size of tarred file convert to blocks (plus 1 to
                    # include header)
                    try:
                        size = self.nti(buf[124:136])
                        blocks = math.ceil(size / float(self.TAR_BLOCKSIZE)) + 1
                    except ValueError as e:
                        is_tar = False
                        break

                    # update file offset for next file in tarball
                    file_offset += int(self.TAR_BLOCKSIZE * blocks)

                    if file_offset >= result.file.size:
                        # we hit the end of the file
                        is_tar = False
                    else:
                        fd.seek(file_offset)
                else:
                    is_tar = False

            result.jump = file_offset
