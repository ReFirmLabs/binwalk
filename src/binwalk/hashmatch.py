import os
import re
import fnmatch
import ctypes
import ctypes.util

import magic
from binwalk.compat import *
from binwalk.common import file_md5

class HashMatch(object):

	# Requires libfuzzy.so
	LIBRARY_NAME = "fuzzy"

	# Max result is 148 (http://ssdeep.sourceforge.net/api/html/fuzzy_8h.html)
	FUZZY_MAX_RESULT = 150
	# Files smaller than this won't produce meaningful fuzzy results (from ssdeep.h)
	FUZZY_MIN_FILE_SIZE = 4096

	FUZZY_DEFAULT_CUTOFF = 50

	def __init__(self, cutoff=None, fuzzy=True, same=False, missing=False, symlinks=False, matches={}, types={}):
		'''
		Class constructor.

		@cutoff          - The fuzzy cutoff which determines if files are different or not.
		@fuzy            - Set to True to do fuzzy hashing; set to False to do traditional hashing.
		@same            - Set to True to show files that are the same, False to show files that are different.
		@missing         - Set to True to show missing files.
		@symlinks        - Set to True to include symbolic link files.
		@matches         - A dictionary of file names to diff.
		@types           - A dictionary of file types to diff.

		Returns None.
		'''
		self.cutoff = cutoff
		self.fuzzy = fuzzy
		self.show_same = same
		self.show_missing = missing
		self.symlinks = symlinks
		self.matches = matches
		self.types = types

		self.magic = magic.open(0)
		self.magic.load()

		self.lib = ctypes.cdll.LoadLibrary(ctypes.util.find_library(self.LIBRARY_NAME))

		if self.cutoff is None:
			self.cutoff = self.FUZZY_DEFAULT_CUTOFF
		
		for k in get_keys(self.types):
			self.types[k] = re.compile(self.types[k])

	def files(self, file1, file2):
		'''
		Fuzzy diff two files.
			
		@file1 - The first file to diff.
		@file2 - The second file to diff.
	
		Returns the match percentage.	
		Returns None on error.
		'''

		if self.fuzzy:
			hash1 = ctypes.create_string_buffer(self.FUZZY_MAX_RESULT)
			hash2 = ctypes.create_string_buffer(self.FUZZY_MAX_RESULT)

			try:
				if self.lib.fuzzy_hash_filename(str2bytes(file1), hash1) == 0 and self.lib.fuzzy_hash_filename(str2bytes(file2), hash2) == 0:
					if hash1.raw == hash2.raw:
						return 100
					else:
						return self.lib.fuzzy_compare(hash1, hash2)
			except Exception as e:
				print "WARNING: Exception while performing fuzzy comparison:", e
		else:
			if file_md5(file1) == file_md5(file2):
				return 100

		return None

	def is_match(self, match):
		'''
		Returns True if the match value is greater than or equal to the cutoff.
		Returns False if the match value is less than the cutoff.
		'''
		return (match >= self.cutoff)

	def _get_file_list(self, directory):
		'''
		Generates a directory tree, including/excluding files as specified in self.matches and self.types.

		@directory - The root directory to start from.

		Returns a set of file paths, excluding the root directory.
		'''
		file_list = []

		# Normalize directory path so that we can exclude it from each individual file path
		directory = os.path.abspath(directory) + os.path.sep

		for (root, dirs, files) in os.walk(directory):
			# Don't include the root directory in the file paths
			root = ''.join(root.split(directory, 1)[1:])

			# Get a list of files, with or without symlinks as specified during __init__
			files = [os.path.join(root, f) for f in files if self.symlinks or not os.path.islink(f)]

			# If no filters were specified, return all files
			if not self.types and not self.matches:
				file_list += files
			else:
				# Filter based on the file type, as reported by libmagic
				if self.types:
					for f in files:
						for (include, type_regex) in iterator(self.types):
							magic_result = self.magic.file(f).lower()
							match = type_regex.match(magic_result)

							# If this matched an include filter, or didn't match an exclude filter
							if (match and include) or (not match and not include):
								file_list.append(f)

				# Filter based on file name
				if self.matches:
					for (include, file_filter) in iterator(self.matches):
						matching_files = fnmatch.filter(files, file_filter)
	
						# If this is an include filter, add all matching files to the list
						if include:
							file_list += matching_files
						# Else, this add all files except those that matched to the list
						else:
							file_list += list(set(files) - set(matching_files))
			
		return set(file_list)

	def directories(self, dir1, dir2):
		results = []

		dir1_files = self._get_file_list(dir1)
		dir2_files = self._get_file_list(dir2)

		for f in dir1_files:
			if f in dir2_files:
				file1 = os.path.join(dir1, f)
				file2 = os.path.join(dir2, f)

				m = self.files(file1, file2)
				matches = self.is_match(m)

				if (matches and self.show_same) or (not matches and not self.show_same):
					results.append(("%3d" % m, f))
	
		if self.show_missing:
			results += [('---', f) for f in (dir1_files-dir2_files)]
			results += [('+++', f) for f in (dir2_files-dir1_files)]

		return results

	def find_file(self, fname, directories):
		pass


if __name__ == '__main__':
	import sys
	
	hmatch = HashMatch(missing=True)
	for (match, fname) in hmatch.directories(sys.argv[1], sys.argv[2]):
		print match, fname

