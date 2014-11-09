import os
import binwalk.core.plugin

class LZMAExtractPlugin(binwalk.core.plugin.Plugin):
    '''
    Gzip extractor plugin.
    '''
    MODULES = ['Signature']

    def init(self):
        import lzma
        self.decompressor = lzma.decompress

        # If the extractor is enabled for the module we're currently loaded
        # into, then register self.extractor as a zlib extraction rule.
        if self.module.extractor.enabled:
            self.module.extractor.add_rule(txtrule=None,
                                           regex="^lzma compressed data",
                                           extension="7z",
                                           cmd=self.extractor)

    def extractor(self, fname):
        fname = os.path.abspath(fname)
        outfile = os.path.splitext(fname)[0]

        try:
            fpin = open(fname, "rb")
            compressed = fpin.read()
            fpin.close()

            decompressed = self.decompressor(compressed)

            fpout = open(outfile, "wb")
            fpout.write(decompressed)
            fpout.close()
        except KeyboardInterrupt as e:
            raise e
        except Exception as e:
            return False

        return True
