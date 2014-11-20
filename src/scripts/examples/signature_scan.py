#!/usr/bin/env python

import sys
import binwalk

try:
    # Perform a signature scan against the files specified on the command line and suppress the usual binwalk output.
    for module in binwalk.scan(*sys.argv[1:], signature=True, quiet=True):
        print ("%s Results:" % module.name)
        for result in module.results:
            print ("\t%s    0x%.8X    %s [%s]" % (result.file.name, result.offset, result.description, str(result.valid)))
except binwalk.ModuleException as e:
    pass
