# Performs raw decompression of various compression algorithms (currently, only deflate).

import os
import binwalk.core.C
from binwalk.core.module import Option, Kwarg, Module

class Deflate(object):
    '''
    Finds and extracts raw deflate compression streams.
    '''

    ENABLED = False
    BLOCK_SIZE = 33*1024
    # To prevent many false positives, only show data that decompressed to a reasonable size and didn't just result in a bunch of NULL bytes
    MIN_DECOMP_SIZE = 32*1024
    DESCRIPTION = "Raw deflate compression stream"

    TINFL_NAME = "tinfl"

    TINFL_FUNCTIONS = [
            binwalk.core.C.Function(name="is_deflated", type=int),
            binwalk.core.C.Function(name="inflate_raw_file", type=None),
    ]

    def __init__(self, module):
        self.module = module

        # The tinfl library is built and installed with binwalk
        self.tinfl = binwalk.core.C.Library(self.TINFL_NAME, self.TINFL_FUNCTIONS)
        
        # Add an extraction rule
        if self.module.extractor.enabled:
            self.module.extractor.add_rule(regex='^%s' % self.DESCRIPTION.lower(), extension="deflate", cmd=self._extractor)

    def _extractor(self, file_name):
        out_file = os.path.splitext(file_name)[0]
        self.tinfl.inflate_raw_file(file_name, out_file)

    def decompress(self, data):
        description = None

        decomp_size = self.tinfl.is_deflated(data, len(data), 0)
        if decomp_size >= self.MIN_DECOMP_SIZE:
            description = self.DESCRIPTION + ', uncompressed size >= %d' % decomp_size

        return description

class RawCompression(Module):

    DECOMPRESSORS = {
            'deflate' : Deflate,
    }

    TITLE = 'Raw Compression'

    CLI = [
            Option(short='X',
                   long='deflate',
                   kwargs={'enabled' : True, 'decompressor_class' : 'deflate'},
                   description='Scan for raw deflate compression streams'),
    ]

    KWARGS = [
            Kwarg(name='enabled', default=False),
            Kwarg(name='decompressor_class', default=None),
    ]

    def init(self):
        self.decompressor = self.DECOMPRESSORS[self.decompressor_class](self)

    def run(self):
        for fp in iter(self.next_file, None):

            fp.set_block_size(peek=self.decompressor.BLOCK_SIZE)

            self.header()

            while True:
                (data, dlen) = fp.read_block()
                if not data:
                    break

                for i in range(0, dlen):
                    description = self.decompressor.decompress(data[i:i+self.decompressor.BLOCK_SIZE])
                    if description:
                        self.result(description=description, file=fp, offset=fp.tell()-dlen+i)

                self.status.completed = fp.tell() - fp.offset

            self.footer()

