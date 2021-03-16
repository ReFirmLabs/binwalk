import struct
import binascii
import binwalk.core.plugin
import binwalk.core.compat
import os
import os.path
import subprocess


class VMLinuxToElfPlugin(binwalk.core.plugin.Plugin):

    '''
    This plugin allows to call "vmlinux-to-elf" on the whole
    file rather than just from some offset of the symbol
    table that was detected.    
    '''
    MODULES = ['Signature']
    current_file = None


    def init(self):
        
        if self.module.extractor.enabled:
            self.module.extractor.add_rule(txtrule=None,
                                           regex="^linux kernel embedded symbol table",
                                           extension="kallsyms",
                                           cmd=self.extractor,
                                           prepend=True)


    def extractor(self, fname):
        fname = os.path.abspath(fname)
        outfile = os.path.splitext(fname)[0] + '_reconstructed.elf'
        fperr = open(os.devnull, "rb")
        
        # Remove the automatically dd'd file which is unuseful
        os.unlink(fname)

        try:
            subprocess.call(['vmlinux-to-elf', self.original_file_path, outfile], stdout = fperr,  stderr =  fperr)
        except KeyboardInterrupt as e:
            raise e
        except Exception as e:
            return False

        return True


    def scan(self, result):
        if result.file and result.description.lower().startswith('linux kernel embedded symbol table'):
            self.original_file_path = result.file.path
            
            



