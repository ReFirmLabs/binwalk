#!/usr/bin/env python

import binwalk

# Since no options are specified, they are by default taken from sys.argv.
# Effecitvely, this duplicates the functionality of the normal binwalk script.
binwalk.scan()
