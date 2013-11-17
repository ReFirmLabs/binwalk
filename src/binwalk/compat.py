# All Python 2/3 compatibility stuffs go here.

from __future__ import print_function
import sys
import string

if sys.version_info.major > 2:
	import urllib.request as urllib2
	string.letters = string.ascii_letters
else:
	import urllib2

def iterator(obj):
	'''
	For cross compatibility between Python 2 and Python 3 dictionaries.
	'''
	if sys.version_info.major > 2:
		return obj.items()
	else:
		return obj.iteritems()
