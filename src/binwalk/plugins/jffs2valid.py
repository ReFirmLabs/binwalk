import binwalk.core.plugin
import binwalk.core.compat
from binwalk.core.common import BlockFile

class JFFS2ValidPlugin(binwalk.core.plugin.Plugin):
    '''
    Helps validate JFFS2 signature results.

    The JFFS2 signature rules catch obvious cases, but inadvertently
    mark some valid JFFS2 nodes as invalid due to  padding (0xFF's or
    0x00's) in between nodes.
    '''
    MODULES = ['Signature']

    MAX_DATA_SIZE = 10240

    def _validate(self, data):
        return data[0:2] in ['\x19\x85', '\x85\x19']

    def scan(self, result):
        if result.file and result.description.lower().startswith('jffs2 filesystem'):

            # Seek to and read the suspected JFFS2 data
            fd = self.module.config.open_file(result.file.name, offset=result.offset+result.jump, length=self.MAX_DATA_SIZE)
            data = fd.read(self.MAX_DATA_SIZE)
            fd.close()

            # Skip any padding
            i = 0
            while i < self.MAX_DATA_SIZE and data[i] in ['\xFF', '\x00']:
                i += 1

            # Did we get to the end of MAX_DATA_SIZE with nothing but padding? Assume valid.
            if i == self.MAX_DATA_SIZE:
                result.valid = True
            # Else, explicitly check for the JFFS2 signature
            else:
                try:
                    result.valid = self._validate(data[i:i+2])
                except IndexError:
                    result.valid = False

