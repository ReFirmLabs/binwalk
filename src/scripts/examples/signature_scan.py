#!/usr/bin/env python

import sys
import binwalk

try:
	for module in binwalk.Modules().execute(*sys.argv[1:], signature=True, quiet=True):
		print ("%s Results:" % module.name)
		for result in module.results:
			print ("\t%s    0x%.8X    %s" % (result.file.name, result.offset, result.description))
except binwalk.ModuleException as e:
	pass
