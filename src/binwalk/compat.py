# All Python 2/3 compatibility stuffs go here.

from __future__ import print_function
import sys
import string

if sys.version_info.major > 2:
	import urllib.request as urllib2
	string.letters = string.ascii_letters
else:
	import urllib2

def iterator(dictionary):
	'''
	For cross compatibility between Python 2 and Python 3 dictionaries.
	'''
	if sys.version_info.major > 2:
		return dictionary.items()
	else:
		return dictionary.iteritems()

def has_key(dictionary, key):
	'''
	For cross compatibility between Python 2 and Python 3 dictionaries.
	'''
	if sys.version_info.major > 2:
		return key in dictionary
	else:
		return dictionary.has_key(key)

def str2bytes(string):
	'''
	For cross compatibility between Python 2 and Python 3 strings.
	'''
	if isinstance(string, type('')) and sys.version_info.major > 2:
		return bytes(string, 'ascii')
	else:
		return string

def bytes2str(bs):
	'''
	For cross compatibility between Python 2 and Python 3 strings.
	'''
	if isinstance(bs, type(b'')) and sys.version_info.major > 2:
		return bs.decode('ascii')
	else:
		return bs

def string_decode(string):
	'''
	For cross compatibility between Python 2 and Python 3 strings.
	'''
	if sys.version_info.major > 2:
		return bytes(string, 'utf-8').decode('unicode_escape')
	else:
		return string.decode('string_escape')

