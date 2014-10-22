# Performs raw decompression of various compression algorithms (currently, only deflate).

import os
import lzma
import struct
import binwalk.core.C
import binwalk.core.compat
from binwalk.core.module import Option, Kwarg, Module

class LZMAHeader(object):
    def __init__(self, **kwargs):
        for (k,v) in binwalk.core.compat.iterator(kwargs):
            setattr(self, k, v)

class LZMA(object):

    DESCRIPTION = "Raw LZMA compression stream"
    FAKE_SIZE = "\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF"
    MAX_PROP = ((4 * 5 + 4) * 9 + 8)
    BLOCK_SIZE = 32*1024

    def __init__(self, module):
        self.module = module

        self.build_properties()
        self.build_dictionaries()
        self.build_headers()

    def build_property(self, pb, lp, lc):
        prop = (((pb * 5) + lp) * 9) + lc
        if prop > self.MAX_PROP:
            prop = None
        return prop

    def parse_property(self, prop):
        prop = int(ord(prop))

        if prop > self.MAX_PROP:
            return None

        pb = prop / (9 * 5);
        prop -= pb * 9 * 5;
        lp = prop / 9;
        lc = prop - lp * 9;

        return (pb, lp, lc)

    def parse_header(self, header):
        (pb, lp, lc) = self.parse_property(header[0])
        dictionary = struct.unpack("<I", binwalk.core.compat.str2bytes(header[1:5]))[0]
        return LZMAHeader(pb=pb, lp=lp, lc=lc, dictionary=dictionary)

    def build_properties(self):
        self.properties = set()

        for pb in range(0, 9):
            for lp in range(0, 5):
                for lc in range(0, 5):
                    prop = self.build_property(pb, lp, lc)
                    if prop is not None:
                        self.properties.add(chr(prop))

    def build_dictionaries(self):
        self.dictionaries = set()

        for n in range(16, 26):
            self.dictionaries.add(binwalk.core.compat.bytes2str(struct.pack("<I", 2**n)))

    def build_headers(self):
        self.headers = set()

        for prop in self.properties:
            for dictionary in self.dictionaries:
                self.headers.add(prop + dictionary + self.FAKE_SIZE)

    def decompress(self, data):
        result = None
        description = None

        for header in self.headers:
            # The only acceptable exceptions are those indicating that the input data was truncated.
            try:
                lzma.decompress(binwalk.core.compat.str2bytes(header + data))
                result = self.parse_header(header)
                break
            except IOError as e:
                # The Python2 module gives this error on truncated input data.
                if str(e) == "unknown BUF error":
                    result = self.parse_header(header)
                    break
            except Exception as e:
                # The Python3 module gives this error on truncated input data.
                # The inconsistency between modules is a bit worrisome.
                if str(e) == "Compressed data ended before the end-of-stream marker was reached":
                    result = self.parse_header(header)
                    break

        if result is not None:
            description = "%s, pb: %d, lp: %d, lc: %d, dictionary size: %d" % (self.DESCRIPTION,
                                                                               result.pb,
                                                                               result.lp,
                                                                               result.lc,
                                                                               result.dictionary)

        return description

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
            self.module.extractor.add_rule(regex='^%s' % self.DESCRIPTION.lower(), extension="deflate", cmd=self.extractor)

    def extractor(self, file_name):
        out_file = os.path.splitext(file_name)[0]
        self.tinfl.inflate_raw_file(file_name, out_file)

    def decompress(self, data):
        description = None

        decomp_size = self.tinfl.is_deflated(data, len(data), 0)
        if decomp_size >= self.MIN_DECOMP_SIZE:
            description = self.DESCRIPTION + ', uncompressed size >= %d' % decomp_size

        return description

class RawCompression(Module):

    TITLE = 'Raw Compression'

    CLI = [
            Option(short='X',
                   long='deflate',
                   kwargs={'enabled' : True, 'scan_for_deflate' : True},
                   description='Scan for raw deflate compression streams'),
            Option(short='Z',
                   long='lzma',
                   kwargs={'enabled' : True, 'scan_for_lzma' : True},
                   description='Scan for raw LZMA compression streams'),
            Option(short='S',
                   long='stop',
                   kwargs={'stop_on_first_hit' : True},
                   description='Stop after the first result'),
    ]

    KWARGS = [
            Kwarg(name='enabled', default=False),
            Kwarg(name='stop_on_first_hit', default=False),
            Kwarg(name='scan_for_deflate', default=False),
            Kwarg(name='scan_for_lzma', default=False),
    ]

    #READ_BLOCK_SIZE = 64*1024

    def init(self):
        self.decompressors = []

        if self.scan_for_deflate:
            self.decompressors.append(Deflate(self))
        if self.scan_for_lzma:
            self.decompressors.append(LZMA(self))

    def run(self):
        for fp in iter(self.next_file, None):

            file_done = False
            #fp.set_block_size(peek=self.READ_BLOCK_SIZE)

            self.header()

            while not file_done:
                (data, dlen) = fp.read_block()
                if not data:
                    break

                for i in range(0, dlen):
                    for decompressor in self.decompressors:
                        description = decompressor.decompress(data[i:i+decompressor.BLOCK_SIZE])
                        if description:
                            self.result(description=description, file=fp, offset=fp.tell()-dlen+i)
                            if self.stop_on_first_hit:
                                file_done = True
                                break

                    if file_done:
                        break

                    self.status.completed += 1

                self.status.completed = fp.tell() - fp.offset

            self.footer()

