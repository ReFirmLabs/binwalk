#!/usr/bin/env python

import sys
import binwalk

# Extracts and logs
for module in binwalk.scan(
        *sys.argv[1:], signature=True, quiet=True, extract=True):
    print ("%s Results:" % module.name)
    for result in module.results:
        if result.file.path in module.extractor.output:
            if result.offset in module.extractor.output[result.file.path].extracted:
                print ("Extracted '%s' at offset 0x%X from '%s' to '%s'" % (result.description.split(',')[0],
                                                                            result.offset,
                                                                            result.file.path,
                                                                            str(module.extractor.output[result.file.path].extracted[result.offset])))
