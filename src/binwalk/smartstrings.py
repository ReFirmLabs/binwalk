import string
import entropy
import plugins
import common

class FileStrings(object):
	'''
	Class for performing a "smart" strings analysis on a single file.
	It is preferred to use the Strings class instead of this class directly.
	'''

	SUSPECT_STRING_LENGTH = 4
	SUSPECT_SPECIAL_CHARS_RATIO = .25
	MIN_STRING_LENGTH = 3
	MAX_STRING_LENGTH = 20
	MAX_SPECIAL_CHARS_RATIO = .4
	MAX_ENTROPY = 0.9

	LETTERS = [x for x in string.letters]
	NUMBERS = [x for x in string.digits]
	PRINTABLE = [x for x in string.printable]
	WHITESPACE = [x for x in string.whitespace]
	PUNCTUATION = [x for x in string.punctuation]
	NEWLINES = ['\r', '\n', '\x0b', '\x0c']
	VOWELS = ['A', 'E', 'I', 'O', 'U', 'a', 'e', 'i', 'o', 'u']
	NON_ALPHA_EXCEPTIONS = ['%', '.', '/', '-', '_']
	BRACKETED = {
			'[' : ']',
			'<' : '>',
			'{' : '}',
			'(' : ')',
	}
	
	def __init__(self, file_name, binwalk, length=0, offset=0, n=MIN_STRING_LENGTH, block=0, algorithm=None, plugins=None):
		'''
		Class constructor. Preferred to be invoked from the Strings class instead of directly.

		@file_name - The file name to perform a strings analysis on.
		@binwalk   - An instance of the Binwalk class.
		@length    - The number of bytes in the file to analyze.
		@offset    - The starting offset into the file to begin analysis.
		@n         - The minimum valid string length.
		@block     - The block size to use when performing entropy analysis.
		@algorithm - The entropy algorithm to use when performing entropy analysis.
		@plugins   - An instance of the Plugins class.

		Returns None.
		'''
		self.n = n
		self.binwalk = binwalk
		self.length = length
		self.start = offset
		self.data = ''
		self.dlen = 0
		self.i = 0
		self.total_read = 0
		self.entropy = {}
		self.valid_strings = []
		self.external_validators = []
		self.plugins = plugins

		if not self.n:
			self.n = self.MIN_STRING_LENGTH

		# Perform an entropy analysis over the entire file (anything less may generate poor entropy data).
		# Give fake file results list to prevent FileEntropy from doing too much analysis.
		with entropy.FileEntropy(file_name, block=block, file_results=['foo']) as e:
			(self.x, self.y, self.average_entropy) = e.analyze()
			for i in range(0, len(self.x)):
				self.entropy[self.x[i]] = self.y[i]
			# Make sure our block size matches the entropy analysis's block size
			self.block = e.block

		# Make sure the starting offset is a multiple of the block size; else, when later checking
		# the entropy analysis, block offsets won't line up.
		self.start -= (self.start % self.block)

		self.fd = common.BlockFile(file_name, 'rb', length=length, offset=self.start)
		# TODO: This is not optimal. We should read in larger chunks and process it into self.block chunks.
		self.fd.READ_BLOCK_SIZE = self.block
		self.fd.MAX_TRAILING_SIZE = 0
		self.start = self.fd.offset

		# Set the total_scanned and scan_length values for plugins and status display messages
		self.binwalk.total_scanned = 0
		self.binwalk.scan_length = self.fd.length

	def __enter__(self):
		return self

	def __del__(self):
		self.cleanup()

	def __exit__(self, t, v, traceback):
		self.cleanup()

	def cleanup(self):
		try:
			self.fd.close()
		except:
			pass

	def _read_block(self):
		'''
		Read one block of data from the target file.

		Returns a tuple of (offset, data_length, data).
		'''
		offset = self.total_read + self.start

		# Ignore blocks which have a higher than average or higher than MAX_ENTROPY entropy
		while self.entropy.has_key(offset):
			# Don't ignore blocks that border on an entropy rising/falling edge
			try:
				if self.entropy[offset-self.block] <= self.MAX_ENTROPY:
					break
				if self.entropy[offset+self.block] <= self.MAX_ENTROPY:
					break
			except KeyError:
				break

			if self.entropy[offset] > self.average_entropy or self.entropy[offset] > self.MAX_ENTROPY:
				self.total_read += self.block
				offset = self.total_read + self.start
				self.fd.seek(offset)
			else:
				break

		(data, dlen) = self.fd.read_block()

		self.binwalk.total_scanned = self.total_read
		self.total_read += dlen

		return (self.start+self.total_read-dlen, dlen, data)

	def _next_byte(self):
		'''
		Grab the next byte from the file.

		Returns a tuple of (offset, byte).
		'''
		byte = ''
		
		# If we've reached the end of the data buffer that we previously read in, read in the next block of data
		if self.i == self.dlen:
			(self.current_offset, self.dlen, self.data) = self._read_block()
			self.i = 0
		
		if self.i < self.dlen:
			byte = self.data[self.i]
			self.i += 1

		return (self.current_offset+self.i-1, byte)

	def _has_vowels(self, data):
		'''
		Returns True if data has a vowel in it, otherwise returns False.
		'''
		for i in self.VOWELS:
			if i in data:
				return True
		return False

	def _alpha_count(self, data):
		'''
		Returns the number of english letters in data.
		'''
		c = 0
		for i in range(0, len(data)):
			if data[i] in self.LETTERS:
				c += 1
		return c

	def _is_bracketed(self, data):
		'''
		Checks if a string is bracketed by special characters.

		@data - The data string to check.

		Returns True if bracketed, False if not.
		'''
		return self.BRACKETED.has_key(data[0]) and data.endswith(self.BRACKETED[data[0]])

	def _non_alpha_count(self, data):
		'''
		Returns the number of non-english letters in data.
		'''
		c = 0
		dlen = len(data)

		# No exceptions for very short strings
		if dlen <= self.SUSPECT_STRING_LENGTH:
			exceptions = []
		else:
			exceptions = self.NON_ALPHA_EXCEPTIONS

		for i in range(0, len(data)):
			if data[i] not in self.LETTERS and data[i] not in self.NUMBERS and data[i] not in exceptions:
					c += 1
		return c

	def _too_many_special_chars(self, data):
		'''
		Returns True if the ratio of special characters in data is too high, otherwise returns False.
		'''
		# If an open bracket exists, we expect a close bracket as well
		for (key, value) in self.BRACKETED.iteritems():
			if key in data and not value in data:
				return True

		# For better filtering of false positives, require a lower ratio of special characters for very short strings
		if len(data) <= self.SUSPECT_STRING_LENGTH:
			return (float(self._non_alpha_count(data)) / len(data)) >= self.SUSPECT_SPECIAL_CHARS_RATIO
		return (float(self._non_alpha_count(data)) / len(data)) >= self.MAX_SPECIAL_CHARS_RATIO

	def _fails_grammar_rules(self, data):
		'''
		Returns True if data fails one of several general grammatical/logical rules.
		'''
		# Nothing here is going to be perfect and will likely result in both false positives and false negatives.
		# The goal however is not to be perfect, but to filter out as many garbage strings while generating as
		# few false negatives as possible.

		# Generally, the first byte of a string is not a punctuation mark
		if data[0] in self.PUNCTUATION:
			return True

		# Some punctuation may be generally considered OK if found at the end of a string; others are very unlikely
		if data[-1] in self.PUNCTUATION and data[-1] not in ['.', '?', ',', '!', '>', '<', '|', '&']:
			return True

		for i in range(0, len(data)):
			try:
				# Q's must be followed by U's
				if data[i] in ['q', 'Q'] and data[i+1] not in ['u', 'U']:
					return True
			except:
				pass

			try:
				# Three characters in a row are the same? Unlikely.
				if data[i] == data[i+1] == data[i+2]:
					return True
			except:
				pass

			try:
				# Three punctuation marks in a row? Unlikely.
				if data[i] in self.PUNCTUATION and data[i+1] in self.PUNCTUATION and data[i+2] in self.PUNCTUATION:
					return True
			except:
				pass

		return False

	def _is_valid(self, offset, string):
		'''
		Determines of a particular string is "valid" or not.

		@string - The string in question.

		Returns True if the string is valid, False if invalid.
		'''
		strlen = len(string)

		for callback in self.external_validators:
			r = callback(offset, string)
			if r is not None:
				return r

		# Large strings are automatically considered valid/interesting
		if strlen >= self.MAX_STRING_LENGTH:
			return True
		elif strlen >= self.n:
			# The chances of a random string being bracketed is pretty low.
			# If the string is bracketed, consider it valid.
			if self._is_bracketed(string):
				return True
			# Else, do some basic sanity checks on the string
			elif self._has_vowels(string):
				if not self._too_many_special_chars(string):
					if not self._fails_grammar_rules(string):
						return True
	
		return False
		
	def _add_string(self, offset, string, plug_pre):
		'''
		Adds a string to the list of valid strings if it passes several rules.
		Also responsible for calling plugin and display callback functions.

		@offset   - The offset at which the string was found.
		@string   - The string that was found.
		@plug_pre - Return value from plugin pre-scan callback functions.

		Returns the value from the plugin callback functions.
		'''
		plug_ret = plugins.PLUGIN_CONTINUE

		string = string.strip()

		if self._is_valid(offset, string):
			results = {'description' : string, 'offset' : offset}

			if self.plugins:
				plug_ret = self.plugins._scan_callbacks(results)
				offset = results['offset']
				string = results['description']

			if not ((plug_ret | plug_pre ) & plugins.PLUGIN_NO_DISPLAY):
				self.binwalk.display.results(offset, [results])
				self.valid_strings.append((offset, string))
		return plug_ret

	def strings(self):
		'''
		Perform a strings analysis on the target file.

		Returns a list of tuples consiting of [(offset, string), (offset, string), ...].
		'''
		string = ''
		string_start = 0
		plugin_pre = plugins.PLUGIN_CONTINUE
		plugin_ret = plugins.PLUGIN_CONTINUE

		if self.plugins:
			plugin_pre = self.plugins._pre_scan_callbacks(self.fd)

		while not ((plugin_pre | plugin_ret) & plugins.PLUGIN_TERMINATE):
			(byte_offset, byte) = self._next_byte()

			# If the returned byte is NULL, try to add whatever string we have now and quit
			if not byte:
				self._add_string(string_start, string, plugin_pre)
				break

			# End of string is signified by a non-printable character or a new line
			if byte in self.PRINTABLE and byte not in self.NEWLINES:
				if not string:
					string_start = byte_offset
				string += byte
			else:
				plugin_ret = self._add_string(string_start, string, plugin_pre)
				string = ''

		if self.plugins:
			self.plugins._post_scan_callbacks(self.fd)

		return self.valid_strings

class Strings(object):
	'''
	Class for performing a strings analysis against a list of files.
	'''

	def __init__(self, file_names, binwalk, length=0, offset=0, n=0, block=0, algorithm=None, load_plugins=True, whitelist=[], blacklist=[]):
		'''
		Class constructor.

		@file_names   - A list of files to analyze.
		@binwalk      - An instance of the Binwalk class.
		@length       - The number of bytes in the file to analyze.
		@offset       - The starting offset into the file to begin analysis.
		@n            - The minimum valid string length.
		@block        - The block size to use when performing entropy analysis.
		@algorithm    - The entropy algorithm to use when performing entropy analysis.
		@load_plugins - Set to False to disable plugin callbacks.
		@whitelist    - A list of whitelisted plugins.
		@blacklist    - A list of blacklisted plugins.

		Returns None.
		'''
		self.file_names = file_names
		self.binwalk = binwalk
		self.length = length
		self.offset = offset
		self.n = n
		self.block = block
		self.algorithm = algorithm
		self.binwalk.scan_type = self.binwalk.STRINGS
		self.file_strings = None

		if load_plugins:
			self.plugins = plugins.Plugins(self.binwalk, whitelist=whitelist, blacklist=blacklist)
		else:
			self.plugins = None

	def __enter__(self):
		return self

	def __exit__(self, t, v, traceback):
		return None

	def add_validator(self, callback):
		'''
		Add a validation function to be invoked when determining if a string is valid or not.
		Validators are passed two arguments: the string offset and the string in question.
		Validators may return:

			o True  - The string is valid, stop further analysis.
			o False - The string is not valid, stop futher analysis.
			o None  - Unknown, continue analysis.

		@callback - The validation function.

		Returns None.
		'''
		if self.file_strings:
			self.file_strings.external_validators.append(callback)

	def strings(self):
		'''
		Perform a "smart" strings analysis against the target files.

		Returns a dictionary compatible with other classes (Entropy, Binwalk, etc):

			{
				'file_name' : (offset, [{
								'description' : 'Strings',
								'string'      : 'found_string'
							}]
					)
			}
		'''
		results = {}

		if self.plugins:
			self.plugins._load_plugins()

		for file_name in self.file_names:
			self.binwalk.display.header(file_name=file_name, description='Strings')
			results[file_name] = []

			self.file_strings = FileStrings(file_name, self.binwalk, self.length, self.offset, self.n, block=self.block, algorithm=self.algorithm, plugins=self.plugins)

			for (offset, string) in self.file_strings.strings():
				results[file_name].append((offset, [{'description' : 'Strings', 'string' : string}]))

			del self.file_strings
			self.file_strings = None

			self.binwalk.display.footer()

		if self.plugins:
			del self.plugins

		return results

