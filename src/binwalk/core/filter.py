import re
import binwalk.core.common as common
from binwalk.core.smart import SmartSignature
from binwalk.core.compat import *

class Filter:
	'''
	Class to filter results based on include/exclude rules and false positive detection.
	An instance of this class is available via the Binwalk.filter object.
	Note that all filter strings should be in lower case.
	'''

	# If the result returned by libmagic is "data" or contains the text
	# 'invalid' or a backslash are known to be invalid/false positives.
	DATA_RESULT = "data"
	INVALID_RESULTS = ["invalid", "\\"]
	INVALID_RESULT = "invalid"
	NON_PRINTABLE_RESULT = "\\"

	FILTER_INCLUDE = 0
	FILTER_EXCLUDE = 1

	def __init__(self, show_invalid_results=False):
		'''
		Class constructor.

		@show_invalid_results - Set to True to display results marked as invalid.

		Returns None.
		'''
		self.filters = []
		self.grep_filters = []
		self.show_invalid_results = show_invalid_results
		self.exclusive_filter = False
		self.smart = SmartSignature(self)

	def include(self, match, exclusive=True):
		'''
		Adds a new filter which explicitly includes results that contain
		the specified matching text.

		@match     - Regex, or list of regexs, to match.
		@exclusive - If True, then results that do not explicitly contain
			     a FILTER_INCLUDE match will be excluded. If False,
			     signatures that contain the FILTER_INCLUDE match will
			     be included in the scan, but will not cause non-matching
			     results to be excluded.
		
		Returns None.
		'''
		if not isinstance(match, type([])):
			matches = [match]
		else:
			matches = match

		for m in matches:
			include_filter = {}

			if m:
				if exclusive and not self.exclusive_filter:
					self.exclusive_filter = True

				include_filter['type'] = self.FILTER_INCLUDE
				include_filter['filter'] = m
				include_filter['regex'] = re.compile(m)
				self.filters.append(include_filter)

	def exclude(self, match):
		'''
		Adds a new filter which explicitly excludes results that contain
		the specified matching text.

		@match - Regex, or list of regexs, to match.
		
		Returns None.
		'''
		if not isinstance(match, type([])):
			matches = [match]
		else:
			matches = match

		for m in matches:
			exclude_filter = {}

			if m:
				exclude_filter['type'] = self.FILTER_EXCLUDE
				exclude_filter['filter'] = m
				exclude_filter['regex'] = re.compile(m)
				self.filters.append(exclude_filter)

	def filter(self, data):
		'''
		Checks to see if a given string should be excluded from or included in the results.
		Called internally by Binwalk.scan().

		@data - String to check.

		Returns FILTER_INCLUDE if the string should be included.
		Returns FILTER_EXCLUDE if the string should be excluded.
		'''
		data = data.lower()

		# Loop through the filters to see if any of them are a match. 
		# If so, return the registered type for the matching filter (FILTER_INCLUDE | FILTER_EXCLUDE). 
		for f in self.filters:
			if f['regex'].search(data):
				return f['type']

		# If there was not explicit match and exclusive filtering is enabled, return FILTER_EXCLUDE.
		if self.exclusive_filter:
			return self.FILTER_EXCLUDE

		return self.FILTER_INCLUDE

	def valid_result(self, data):
		'''
		Checks if the given string contains invalid data.

		@data - String to validate.

		Returns True if data is valid, False if invalid.
		'''
		# A result of 'data' is never ever valid (for libmagic results)
		if data == self.DATA_RESULT:
			return False

		# Make sure this result wasn't filtered
		if self.filter(data) == self.FILTER_EXCLUDE:
			return False

		# If showing invalid results, just return True without further checking.
		if self.show_invalid_results:
			return True

		# Don't include quoted strings or keyword arguments in this search, as 
		# strings from the target file may legitimately contain the INVALID_RESULT text.
		if self.INVALID_RESULT in common.strip_quoted_strings(self.smart._strip_tags(data)):
			return False

		# There should be no non-printable characters in any of the data
		if self.NON_PRINTABLE_RESULT in data:
			return False

		return True

	def grep(self, data=None, filters=[]):
		'''
		Add or check case-insensitive grep filters against the supplied data string.

		@data    - Data string to check grep filters against. Not required if filters is specified.
		@filters - Regex, or list of regexs, to add to the grep filters list. Not required if data is specified.

		Returns None if data is not specified.
		If data is specified, returns True if the data contains a grep filter, or if no grep filters exist.
		If data is specified, returns False if the data does not contain any grep filters.
		'''
		# Add any specified filters to self.grep_filters
		if filters:
			if not isinstance(filters, type([])):
				gfilters = [filters]
			else:
				gfilters = filters

			for gfilter in gfilters:
				# Filters are case insensitive
				self.grep_filters.append(re.compile(gfilter))

		# Check the data against all grep filters until one is found
		if data is not None:
			# If no grep filters have been created, always return True
			if not self.grep_filters:
				return True

			# Filters are case insensitive
			data = data.lower()

			# If a filter exists in data, return True
			for gfilter in self.grep_filters:
				if gfilter.search(data):
					return True

			# Else, return False
			return False
	
		return None

	def clear(self):
		'''
		Clears all include, exclude and grep filters.
		
		Retruns None.
		'''
		self.filters = []
		self.grep_filters = []
