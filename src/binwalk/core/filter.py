# Code for filtering of results (e.g., removing invalid results)

import re
import binwalk.core.common as common
from binwalk.core.smart import Signature
from binwalk.core.compat import *

class FilterType(object):

    FILTER_INCLUDE = 0
    FILTER_EXCLUDE = 1

    def __init__(self, **kwargs):
        self.type = None
        self.filter = None
        self.regex = None

        for (k,v) in iterator(kwargs):
            setattr(self, k, v)

        if self.regex is None:
            self.regex = re.compile(self.filter)

class FilterInclude(FilterType):

    def __init__(self, **kwargs):
        super(FilterInclude, self).__init__(**kwargs)
        self.type = self.FILTER_INCLUDE

class FilterExclude(FilterType):

    def __init__(self, **kwargs):
        super(FilterExclude, self).__init__(**kwargs)
        self.type = self.FILTER_EXCLUDE

class Filter(object):
    '''
    Class to filter results based on include/exclude rules and false positive detection.
    Note that all filter strings should be in lower case.
    '''

    # If the result returned by libmagic is "data" or contains the text
    # 'invalid' or a backslash are known to be invalid/false positives.
    UNKNOWN_RESULTS = ["data", "very short file (no magic)"]
    INVALID_RESULT = "invalid"
    NON_PRINTABLE_RESULT = "\\"

    def __init__(self, show_invalid_results=None):
        '''
        Class constructor.

        @show_invalid_results - A function to call that will return True to display results marked as invalid.

        Returns None.
        '''
        self.filters = []
        self.grep_filters = []
        self.show_invalid_results = show_invalid_results
        self.exclusive_filter = False
        self.smart = Signature(self)

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
            if m:
                if exclusive and not self.exclusive_filter:
                    self.exclusive_filter = True

                self.filters.append(FilterInclude(filter=m))

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
            if m:
                self.filters.append(FilterExclude(filter=m))

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
        # If so, return the registered type for the matching filter (FILTER_INCLUDE || FILTER_EXCLUDE).
        for f in self.filters:
            if f.regex.search(data):
                return f.type

        # If there was not explicit match and exclusive filtering is enabled, return FILTER_EXCLUDE.
        if self.exclusive_filter:
            return FilterType.FILTER_EXCLUDE

        return FilterType.FILTER_INCLUDE

    def valid_result(self, data):
        '''
        Checks if the given string contains invalid data.

        @data - String to validate.

        Returns True if data is valid, False if invalid.
        '''
        # A result of 'data' is never ever valid (for libmagic results)
        if data in self.UNKNOWN_RESULTS:
            return False

        # Make sure this result wasn't filtered
        if self.filter(data) == FilterType.FILTER_EXCLUDE:
            return False

        # If showing invalid results, just return True without further checking.
        if self.show_invalid_results:
            return True

        # Sanitized data contains only the non-quoted portion of the data
        sanitized_data = common.strip_quoted_strings(self.smart.strip_tags(data))

        # Don't include quoted strings or keyword arguments in this search, as
        # strings from the target file may legitimately contain the INVALID_RESULT text.
        if self.INVALID_RESULT in sanitized_data:
            return False

        # There should be no non-printable characters in any of the quoted string data
        non_printables_raw = set(re.findall("\\\\\d{3}", data))
        non_printables_sanitized = set(re.findall("\\\\d{3}", sanitized_data))
        if len(non_printables_raw) and non_printables_raw != non_printables_sanitized:
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
