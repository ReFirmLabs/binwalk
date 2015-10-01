#import binwalk.core.C
import binwalk.core.plugin
#from binwalk.core.common import *

class CompressdPlugin(binwalk.core.plugin.Plugin):
#    '''
#    Searches for and validates compress'd data.
#    '''

    MODULES = ['Signature']

    #READ_SIZE = 64

    #COMPRESS42 = "compress42"
    #COMPRESS42_FUNCTIONS = [
    #    binwalk.core.C.Function(name="is_compressed", type=bool),
    #]

    #comp = None

    #def init(self):
        #self.comp = binwalk.core.C.Library(self.COMPRESS42, self.COMPRESS42_FUNCTIONS)
        # This plugin is currently disabled due to the need to move away from supporting C
        # libraries and into a pure Python project, for cross-platform support and ease of
        # installation / package maintenance. A Python implementation will likely need to
        # be custom developed in the future, but for now, since this compression format is
        # not very common, especially in firmware, simply disable it.
        #self.comp = None

    #def scan(self, result):
    #    if self.comp and result.file and result.description.lower().startswith("compress'd data"):
    #        fd = self.module.config.open_file(result.file.name, offset=result.offset, length=self.READ_SIZE)
    #        compressed_data = fd.read(self.READ_SIZE)
    #        fd.close()

    #        if not self.comp.is_compressed(compressed_data, len(compressed_data)):
    #            result.valid = False


