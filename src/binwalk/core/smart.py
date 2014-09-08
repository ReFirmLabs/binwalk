# "Smart" parser for handling libmagic signature results. Specifically, this implements
# support for binwalk's custom libmagic signature extensions (keyword tags, string processing,
# false positive detection, etc).

import re
import binwalk.core.module
from binwalk.core.compat import *
from binwalk.core.common import get_quoted_strings, MathExpression

class Tag(object):

    TAG_DELIM_START = "{"
    TAG_DELIM_END = "}"
    TAG_ARG_SEPERATOR = ":"

    def __init__(self, **kwargs):
        self.name = None
        self.keyword = None
        self.type = None
        self.handler = None
        self.tag = None
        self.default = None

        for (k,v) in iterator(kwargs):
            setattr(self, k, v)

        if self.type == int:
            self.default = 0
        elif self.type == str:
            self.default = ''

        if self.keyword is not None:
            self.tag = self.TAG_DELIM_START + self.keyword
            if self.type is None:
                self.tag += self.TAG_DELIM_END
            else:
                self.tag += self.TAG_ARG_SEPERATOR

        if self.handler is None:
            if self.type == int:
                self.handler = 'get_math_arg'
            elif self.type == str:
                self.handler = 'get_keyword_arg'

class Signature(object):
    '''
    Class for parsing smart signature tags in libmagic result strings.

    This class is intended for internal use only, but a list of supported 'smart keywords' that may be used
    in magic files is available via the SmartSignature.KEYWORDS dictionary:

        from binwalk import SmartSignature

        for tag in SmartSignature.TAGS:
            print tag.keyword
    '''

    TAGS = [
        Tag(name='raw-string', keyword='raw-string', type=str, handler='parse_raw_string'),
        Tag(name='string-len', keyword='string-len', type=str, handler='parse_string_len'),
        Tag(name='math', keyword='math', type=int, handler='parse_math'),
        Tag(name='one-of-many', keyword='one-of-many', handler='one_of_many'),
        Tag(name='display-once', keyword='display-once', handler='display_once'),

        Tag(name='jump', keyword='jump-to-offset', type=int),
        Tag(name='name', keyword='file-name', type=str),
        Tag(name='size', keyword='file-size', type=int),
        Tag(name='adjust', keyword='offset-adjust', type=int),
        Tag(name='delay', keyword='extract-delay', type=str),
        Tag(name='year', keyword='file-year', type=str),
        Tag(name='epoch', keyword='file-epoch', type=int),

        Tag(name='raw-size', keyword='raw-string-length', type=int),
        Tag(name='raw-replace', keyword='raw-replace'),
        Tag(name='string-len-replace', keyword='string-len'),
    ]

    def __init__(self, filter, ignore_smart_signatures=False):
        '''
        Class constructor.

        @filter                  - Instance of the MagicFilter class.
        @ignore_smart_signatures - Set to True to ignore smart signature keywords.

        Returns None.
        '''
        self.filter = filter
        self.last_one_of_many = None
        self.valid_once_already_seen = set()
        self.ignore_smart_signatures = ignore_smart_signatures

    def parse(self, data):
        '''
        Parse a given data string for smart signature keywords. If any are found, interpret them and strip them.

        @data - String to parse, as returned by libmagic.

        Returns a dictionary of parsed values.
        '''
        results = {}
        self.valid = True
        self.display = True

        if data:
            for tag in self.TAGS:
                if tag.handler is not None:
                    (d, arg) = getattr(self, tag.handler)(data, tag)
                    if not self.ignore_smart_signatures:
                        data = d

                    if isinstance(arg, type(False)) and arg == False and not self.ignore_smart_signatures:
                        self.valid = False
                    elif tag.type is not None:
                        if self.ignore_smart_signatures:
                            results[tag.name] = tag.default
                        else:
                            results[tag.name] = arg

            if self.ignore_smart_signatures:
                results['description'] = data
            else:
                results['description'] = self.strip_tags(data)
        else:
            self.valid = False

        results['valid'] = self.valid
        results['display'] = self.display

        return binwalk.core.module.Result(**results)

    def tag_lookup(self, keyword):
        for tag in self.TAGS:
            if tag.keyword == keyword:
                return tag
        return None

    def is_valid(self, data):
        '''
        Validates that result data does not contain smart keywords in file-supplied strings.

        @data - Data string to validate.

        Returns True if data is OK.
        Returns False if data is not OK.
        '''
        # All strings printed from the target file should be placed in strings, else there is
        # no way to distinguish between intended keywords and unintended keywords. Get all the
        # quoted strings.
        quoted_data = get_quoted_strings(data)

        # Check to see if there was any quoted data, and if so, if it contained the keyword starting delimiter
        if quoted_data and Tag.TAG_DELIM_START in quoted_data:
            # If so, check to see if the quoted data contains any of our keywords.
            # If any keywords are found inside of quoted data, consider the keywords invalid.
            for tag in self.TAGS:
                if tag.tag in quoted_data:
                    return False
        return True

    def safe_string(self, data):
        '''
        Strips out quoted data (i.e., data taken directly from a file).
        '''
        quoted_string = get_quoted_strings(data)
        if quoted_string:
            data = data.replace('"' + quoted_string + '"', "")
        return data

    def display_once(self, data, tag):
        '''
        Determines if a given data string should be printed if {display-once} was specified.

        @data - String result data.

        Returns False if the string result should not be displayed.
        Returns True if the string result should be displayed.
        '''
        if self.filter.valid_result(data):
            signature = data.split(',')[0]
            if signature in self.valid_once_already_seen:
                self.display = False
                return (data, False)
            elif tag.tag in data:
                self.valid_once_already_seen.add(signature)
                return (data, True)

        return (data, True)

    def one_of_many(self, data, tag):
        '''
        Determines if a given data string is one result of many.

        @data - String result data.

        Returns False if the string result is one of many and should not be displayed.
        Returns True if the string result is not one of many and should be displayed.
        '''
        if self.filter.valid_result(data):
            if self.last_one_of_many is not None and data.startswith(self.last_one_of_many):
                self.display = False
            elif tag.tag in data:
                # Only match on the data before the first comma, as that is typically unique and static
                self.last_one_of_many = data.split(',')[0]
            else:
                self.last_one_of_many = None

        return (data, True)

    def get_keyword_arg(self, data, tag):
        '''
        Retrieves the argument for keywords that specify arguments.

        @data    - String result data, as returned by libmagic.
        @keyword - Keyword index in KEYWORDS.

        Returns the argument string value on success.
        Returns a blank string on failure.
        '''
        arg = ''
        safe_data = self.safe_string(data)

        if tag.tag in safe_data:
            arg = safe_data.split(tag.tag)[1].split(tag.TAG_DELIM_END)[0]

        return (data, arg)

    def get_math_arg(self, data, tag):
        '''
        Retrieves the argument for keywords that specifiy mathematical expressions as arguments.

        @data    - String result data, as returned by libmagic.
        @keyword - Keyword index in KEYWORDS.

        Returns the resulting calculated value.
        '''
        value = 0

        (data, arg) = self.get_keyword_arg(data, tag)
        if arg:
            value = MathExpression(arg).value
            if value is None:
                value = 0
                self.valid = False

        return (data, value)

    def parse_math(self, data, tag):
        '''
        Replace math keywords with the requested values.

        @data - String result data.

        Returns the modified string result data.
        '''
        while tag.tag in self.safe_string(data):
            (data, arg) = self.get_keyword_arg(data, tag)
            v = '%s%s%s' % (tag.tag, arg, tag.TAG_DELIM_END)
            (data, math_value) = self.get_math_arg(data, tag)
            data = data.replace(v, "%d" % math_value)

        return (data, None)

    def parse_raw_string(self, data, raw_str_tag):
        '''
        Process strings that aren't NULL byte terminated, but for which we know the string length.
        This should be called prior to any other smart parsing functions.

        @data - String to parse.

        Returns a parsed string.
        '''
        if self.is_valid(data):
            raw_str_length_tag = self.tag_lookup('raw-string-length')
            raw_replace_tag = self.tag_lookup('raw-replace')

            # Get the raw string  keyword arg
            (data, raw_string) = self.get_keyword_arg(data, raw_str_tag)

            # Was a raw string keyword specified?
            if raw_string:
                # Get the raw string length arg
                (data, raw_size) = self.get_math_arg(data, raw_str_length_tag)

                # Replace all instances of raw-replace in data with raw_string[:raw_size]
                # Also strip out everything after the raw-string keyword, including the keyword itself.
                # Failure to do so may (will) result in non-printable characters and this string will be
                # marked as invalid when it shouldn't be.
                data = data[:data.find(raw_str_tag.tag)].replace(raw_replace_tag.tag, '"' + raw_string[:raw_size] + '"')

        return (data, True)

    def parse_string_len(self, data, str_len_tag):
        '''
        Process {string-len} macros.

        @data - String to parse.

        Returns parsed data string.
        '''
        if not self.ignore_smart_signatures and self.is_valid(data):

            str_len_replace_tag = self.tag_lookup('string-len-replace')

            # Get the raw string  keyword arg
            (data, raw_string) = self.get_keyword_arg(data, str_len_tag)

            # Was a string-len  keyword specified?
            if raw_string:
                # Get the string length
                try:
                    string_length = '%d' % len(raw_string)
                except KeyboardInterrupt as e:
                    raise e
                except Exception:
                    string_length = '0'

                # Strip out *everything* after the string-len keyword, including the keyword itself.
                # Failure to do so can potentially allow keyword injection from a maliciously created file.
                data = data.split(str_len_tag.tag)[0].replace(str_len_replace_tag.tag, string_length)

        return (data, True)

    def strip_tags(self, data):
        '''
        Strips the smart tags from a result string.

        @data - String result data.

        Returns a sanitized string.
        '''
        if not self.ignore_smart_signatures:
            for tag in self.TAGS:
                start = data.find(tag.tag)
                if start != -1:
                    end = data[start:].find(tag.TAG_DELIM_END)
                    if end != -1:
                        data = data.replace(data[start:start+end+1], "")
        return data

