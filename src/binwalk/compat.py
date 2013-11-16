# All Python 2/3 compatibility stuffs go here.

from __future__ import print_function
import sys
import string

if sys.version_info.major > 2:
	import urllib.request as urllib2
	string.letters = string.ascii_letters
else:
	import urllib2
