#!/usr/bin/env python

import sys
import ctypes
import ctypes.util

SIZE = 64

try:
	data = open(sys.argv[1], "rb").read(SIZE)
except:
	print "Usage: %s <input file>" % sys.argv[0]
	sys.exit(1)

comp = ctypes.cdll.LoadLibrary(ctypes.util.find_library("compress42"))

if comp.is_compressed(data, len(data)):
	print "%s is compress'd." % (sys.argv[1])
else:
	print "%s is not compress'd." % sys.argv[1]
