import os
import shutil
import binwalk.core.plugin
from binwalk.core.compat import *
from binwalk.core.common import BlockFile

class LZMAModPlugin(binwalk.core.plugin.Plugin):
    '''
    Finds and extracts modified LZMA files commonly found in cable modems.
    Based on Bernardo Rodrigues' work: http://w00tsec.blogspot.com/2013/11/unpacking-firmware-images-from-cable.html
    '''
    MODULES = ['Signature']

    FAKE_LZMA_SIZE = "\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF"
    SIGNATURE = "lzma compressed data"

    def init(self):
        self.original_cmd = ''

        # Replace the first existing LZMA extraction command with our own
        for rule in self.module.extractor.match(self.SIGNATURE):
            self.original_cmd = rule['cmd']
            rule['cmd'] = self.lzma_cable_extractor
            break

    def lzma_cable_extractor(self, fname):
        # Try extracting the LZMA file without modification first
        result = self.module.extractor.execute(self.original_cmd, fname)

        # If the external extractor was successul (True) or didn't exist (None), don't do anything.
        if result not in [True, None]:
            out_name = os.path.splitext(fname)[0] + '-patched' + os.path.splitext(fname)[1]
            fp_out = BlockFile(out_name, 'w')
            # Use self.module.config.open_file here to ensure that other config settings (such as byte-swapping) are honored
            fp_in = self.module.config.open_file(fname, offset=0, length=0)
            fp_in.set_block_size(peek=0)
            i = 0

            while i < fp_in.length:
                (data, dlen) = fp_in.read_block()

                if i == 0:
                    out_data = data[0:5] + self.FAKE_LZMA_SIZE + data[5:]
                else:
                    out_data = data

                fp_out.write(out_data)

                i += dlen

            fp_in.close()
            fp_out.close()

            # Overwrite the original file so that it can be cleaned up if -r was specified
            shutil.move(out_name, fname)
            result = self.module.extractor.execute(self.original_cmd, fname)

        return result

    def scan(self, result):
        # The modified cable modem LZMA headers all have valid dictionary sizes and a properties byte of 0x5D.
        if result.description.lower().startswith(self.SIGNATURE) and "invalid uncompressed size" in result.description:
            if "properties: 0x5D" in result.description and "invalid dictionary size" not in result.description:
                result.valid = True
                result.description = result.description.split("invalid uncompressed size")[0] + "missing uncompressed size"

