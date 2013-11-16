#!/usr/bin/env python

import sys
import ctypes
import ctypes.util

SIZE = 33*1024

try:
	data = open(sys.argv[1], "rb").read(SIZE)
except:
	print "Usage: %s <input file>" % sys.argv[0]
	sys.exit(1)

tinfl = ctypes.cdll.LoadLibrary(ctypes.util.find_library("tinfl"))

if tinfl.is_deflated(data, len(data), 0):
	print "%s is deflated." % (sys.argv[1])
	print "Inflated to %d bytes!" % tinfl.inflate_raw_file(sys.argv[1], sys.argv[1] + '.inflated')
else:
	print "%s is not deflated." % sys.argv[1]
