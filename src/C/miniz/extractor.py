#!/usr/bin/env python

import sys
import ctypes
import ctypes.util
from binwalk.common import BlockFile

class Foo:
	SIZE = 33*1024

	def __init__(self):
		self.tinfl = ctypes.cdll.LoadLibrary(ctypes.util.find_library("tinfl"))

        def _extractor(self, file_name):
		processed = 0
                inflated_data = ''
                fd = BlockFile(file_name, 'rb')
                fd.READ_BLOCK_SIZE = self.SIZE

                while processed < fd.length:
                        (data, dlen) = fd.read_block()

                        inflated_block = self.tinfl.inflate_block(data, dlen)
                        if inflated_block:
                                inflated_data += ctypes.c_char_p(inflated_block).value[0:4]
                        else:
                                break

			processed += dlen

                fd.close()

		print inflated_data
                print "%s inflated to %d bytes" % (file_name, len(inflated_data))

Foo()._extractor(sys.argv[1])
