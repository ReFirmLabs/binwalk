import os
import zlib
import binwalk.core.common
import binwalk.core.plugin
from binwalk.core.compat import str2bytes


class ZLIBExtractPlugin(binwalk.core.plugin.Plugin):

    '''
    Zlib extractor plugin.
    '''
    MODULES = ['Signature']

    def init(self):
        # If the extractor is enabled for the module we're currently loaded
        # into, then register self.extractor as a zlib extraction rule.
        if self.module.extractor.enabled:
            self.module.extractor.add_rule(txtrule=None,
                                           regex="^zlib compressed data",
                                           extension="zlib",
                                           cmd=self.extractor)

    def extractor(self, fname):
        outfile = os.path.splitext(fname)[0]

        try:
            fpin = binwalk.core.common.BlockFile(fname)
            fpout = binwalk.core.common.BlockFile(outfile, 'w')

            plaintext = zlib.decompress(str2bytes(fpin.read()))
            fpout.write(plaintext)

            fpin.close()
            fpout.close()
        except KeyboardInterrupt as e:
            raise e
        except Exception as e:
            return False

        return True
