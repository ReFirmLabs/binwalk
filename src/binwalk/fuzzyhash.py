import ctypes
import ctypes.util
from binwalk.compat import *

class FuzzyHash(object):

	# Requires libfuzzy.so
	LIBRARY_NAME = "fuzzy"

	# Max result is 148 (http://ssdeep.sourceforge.net/api/html/fuzzy_8h.html)
	FUZZY_MAX_RESULT = 150

	def __init__(self):
		self.lib = ctypes.cdll.LoadLibrary(ctypes.util.find_library(self.LIBRARY_NAME))

	def compare_files(self, file1, file2):
		hash1 = ctypes.create_string_buffer(self.FUZZY_MAX_RESULT)
		hash2 = ctypes.create_string_buffer(self.FUZZY_MAX_RESULT)

		if self.lib.fuzzy_hash_filename(str2bytes(file1), hash1) == 0 and self.lib.fuzzy_hash_filename(str2bytes(file2), hash2) == 0:
			return self.lib.fuzzy_compare(hash1, hash2)

		return None


if __name__ == '__main__':
	import sys
	
	print (FuzzyHash().compare_files(sys.argv[1], sys.argv[2]))
