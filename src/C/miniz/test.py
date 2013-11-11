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

if tinfl.is_deflated(data, len(data), 1):
	print "%s is zlib compressed." % (sys.argv[1])
else:
	print "%s is not zlib compressed." % sys.argv[1]
