import os
import re
import magic
import fnmatch
import ctypes
import ctypes.util
import binwalk.smartstrings
from binwalk.compat import *
from binwalk.common import strings
from binwalk.prettyprint import PrettyPrint

class HashResult(object):
	'''
	Class for storing libfuzzy hash results.
	For internal use only.
	'''

	def __init__(self, name, hash=None, strings=None):
		self.name = name
		self.hash = hash
		self.strings = strings

class HashMatch(object):
	'''
	Class for fuzzy hash matching of files and directories.
	'''
	# Requires libfuzzy.so
	LIBRARY_NAME = "fuzzy"

	# Max result is 148 (http://ssdeep.sourceforge.net/api/html/fuzzy_8h.html)
	FUZZY_MAX_RESULT = 150
	# Files smaller than this won't produce meaningful fuzzy results (from ssdeep.h)
	FUZZY_MIN_FILE_SIZE = 4096

	DEFAULT_CUTOFF = 0
	CONSERVATIVE_CUTOFF = 90

	def __init__(self, cutoff=None, strings=False, same=False, symlinks=False, name=False, max_results=None, display=False, log=None, csv=False, quiet=False, format_to_screen=False, abspath=False, matches={}, types={}):
		'''
		Class constructor.

		@cutoff           - The fuzzy cutoff which determines if files are different or not.
		@strings          - Only hash strings inside of the file, not the entire file itself.
		@same             - Set to True to show files that are the same, False to show files that are different.
		@symlinks         - Set to True to include symbolic link files.
		@name             - Set to True to only compare files whose base names match.
		@max_results      - Stop searching after x number of matches.
		@display          - Set to True to display results to stdout, or pass an instance of binwalk.prettyprint.PrettyPrint.
		@log              - Specify a log file to log results to.
		@csv              - Set to True to log data in CSV format.
		@quiet            - Set to True to suppress output to stdout.
		@format_to_screen - Set to True to format the output to the terminal window width.
		@abspath          - Set to True to display absolute file paths.
		@matches          - A dictionary of file names to diff.
		@types            - A dictionary of file types to diff.

		Returns None.
		'''
		self.cutoff = cutoff
		self.strings = strings
		self.show_same = same
		self.symlinks = symlinks
		self.matches = matches
		self.name = name
		self.types = types
		self.abspath = abspath
		self.max_results = max_results

		if display:
			if isinstance(display, PrettyPrint):
				self.pretty_print = display
			else:
				self.pretty_print = PrettyPrint(log=log, csv=csv, format_to_screen=format_to_screen, quiet=quiet)

			self.pretty_print.header(header="PERCENTAGE\t\t\tFILE", csv=True)
		else:
			self.pretty_print = None

		self.total = 0
		self.last_file1 = HashResult(None)
		self.last_file2 = HashResult(None)

		self.magic = magic.open(0)
		self.magic.load()

		lib_path = ctypes.util.find_library(self.LIBRARY_NAME)
		if lib_path is None:
			raise Exception('Could not find the hash matching library. Please install libfuzzy from ssdeep.')
		self.lib = ctypes.cdll.LoadLibrary(lib_path)

		if self.cutoff is None:
			self.cutoff = self.DEFAULT_CUTOFF
		
		for k in get_keys(self.types):
			for i in range(0, len(self.types[k])):
				self.types[k][i] = re.compile(self.types[k][i])

	def _get_strings(self, fname):
		return ''.join(list(binwalk.common.strings(fname, minimum=10)))

	def _print(self, match, fname):
		if self.pretty_print:
			if self.abspath:
				fname = os.path.abspath(fname)
			self.pretty_print._pprint('%4d\t\t\t\t%s\n' % (match, self.pretty_print._format(fname)))

	def _print_footer(self):
		if self.pretty_print:
			self.pretty_print.footer()

	def _compare_files(self, file1, file2):
		'''
		Fuzzy diff two files.
			
		@file1 - The first file to diff.
		@file2 - The second file to diff.
	
		Returns the match percentage.	
		Returns None on error.
		'''
		status = 0
		file1_dup = False
		file2_dup = False

		if not self.name or os.path.basename(file1) == os.path.basename(file2):
			if os.path.exists(file1) and os.path.exists(file2):

				hash1 = ctypes.create_string_buffer(self.FUZZY_MAX_RESULT)
				hash2 = ctypes.create_string_buffer(self.FUZZY_MAX_RESULT)

				# Check if the last file1 or file2 matches this file1 or file2; no need to re-hash if they match.
				if file1 == self.last_file1.name and self.last_file1.hash:
					file1_dup = True
				else:
					self.last_file1.name = file1

				if file2 == self.last_file2.name and self.last_file2.hash:
					file2_dup = True
				else:
					self.last_file2.name = file2

				try:
					if self.strings:
						if file1_dup:
							file1_strings = self.last_file1.strings
						else:
							self.last_file1.strings = file1_strings = self._get_strings(file1)
							
						if file2_dup:
							file2_strings = self.last_file2.strings
						else:
							self.last_file2.strings = file2_strings = self._get_strings(file2)

						if file1_strings == file2_strings:
							return 100
						else:
							if file1_dup:
								hash1 = self.last_file1.hash
							else:
								status |= self.lib.fuzzy_hash_buf(str2bytes(file1_strings), len(file1_strings), hash1)

							if file2_dup:
								hash2 = self.last_file2.hash
							else:
								status |= self.lib.fuzzy_hash_buf(str2bytes(file2_strings), len(file2_strings), hash2)
						
					else:
						if file1_dup:
							hash1 = self.last_file1.hash
						else:
							status |= self.lib.fuzzy_hash_filename(str2bytes(file1), hash1)
							
						if file2_dup:
							hash2 = self.last_file2.hash
						else:
							status |= self.lib.fuzzy_hash_filename(str2bytes(file2), hash2)
				
					if status == 0:
						if not file1_dup:
							self.last_file1.hash = hash1
						if not file2_dup:
							self.last_file2.hash = hash2

						if hash1.raw == hash2.raw:
							return 100
						else:
							return self.lib.fuzzy_compare(hash1, hash2)
				except Exception as e:
					print ("WARNING: Exception while doing fuzzy hash: %s" % e)

		return None

	def is_match(self, match):
		'''
		Returns True if this is a good match.
		Returns False if his is not a good match.
		'''
		return (match is not None and ((match >= self.cutoff and self.show_same) or (match < self.cutoff and not self.show_same)))

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
						for (include, regex_list) in iterator(self.types):
							for regex in regex_list:
								try:
									magic_result = self.magic.file(os.path.join(directory, f)).lower()
								except Exception as e:
									magic_result = ''

								match = regex.match(magic_result)

								# If this matched an include filter, or didn't match an exclude filter
								if (match and include) or (not match and not include):
									file_list.append(f)

				# Filter based on file name
				if self.matches:
					for (include, file_filter_list) in iterator(self.matches):
						for file_filter in file_filter_list:
							matching_files = fnmatch.filter(files, file_filter)
	
							# If this is an include filter, add all matching files to the list
							if include:
								file_list += matching_files
							# Else, this add all files except those that matched to the list
							else:
								file_list += list(set(files) - set(matching_files))
			
		return set(file_list)

	def files(self, needle, haystack):
		'''
		Compare one file against a list of other files.
		
		@needle   - File to match against.
		@haystack - A list of haystack files.
	
		Returns a list of tuple results.
		'''
		results = []
		self.total = 0

		for f in haystack:
			m = self._compare_files(needle, f)
			if m is not None and self.is_match(m):
				self._print(m, f)
				results.append((m, f))
					
				self.total += 1
				if self.max_results and self.total >= self.max_results:
					break

		self._print_footer()
		return results

	def file(self, needle, haystack):
		'''
		Search for one file inside one or more directories.

		@needle   - File to search for.
		@haystack - List of directories to search in.

		Returns a list of tuple results.
		'''
		matching_files = []
		self.total = 0
		done = False

		for directory in haystack:
			for f in self._get_file_list(directory):
				f = os.path.join(directory, f)
				m = self._compare_files(needle, f)
				if m is not None and self.is_match(m):
					self._print(m, f)
					matching_files.append((m, f))
					
					self.total += 1
					if self.max_results and self.total >= self.max_results:
						done = True
						break
			if done:
				break
					
		self._print_footer()
		return matching_files
	
	def directories(self, needle, haystack):
		'''
		Compare the contents of one directory with the contents of other directories.

		@source   - Source directory to compare everything to.
		@dir_list - Compare files in source to files in these directories.

		Returns a list of tuple results.
		'''
		done = False
		results = []
		self.total = 0

		source_files = self._get_file_list(needle)

		for directory in haystack:
			dir_files = self._get_file_list(directory)
		
			for f in source_files:
				if f in dir_files:
					file1 = os.path.join(needle, f)
					file2 = os.path.join(directory, f)

					m = self._compare_files(file1, file2)
					if m is not None and self.is_match(m):
						self._print(m, file2)
						results.append((m, file2))

						self.total += 1
						if self.max_results and self.total >= self.max_results:
							done = True
							break
			if done:
				break

		self._print_footer()
		return results


if __name__ == '__main__':
	import sys
	
	hmatch = HashMatch(strings=True, name=False, types={True:"^elf"})
	print (hmatch.file(sys.argv[1], sys.argv[2:]))
	#for (match, fname) in hmatch.directories(sys.argv[1], sys.argv[2]):
	#for (match, fname) in hmatch.find_file(sys.argv[1], sys.argv[2:]):
	#	print match, fname

