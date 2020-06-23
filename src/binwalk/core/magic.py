# A pure Python replacement for libmagic. Supports most libmagic features, plus
# several additional features not provided by libmagic. Tailored specifically
# for quickly searching blocks of data for multiple embedded signatures.

__all__ = ['Magic']

import re
import struct
import datetime
import binwalk.core.common
import binwalk.core.compat
from binwalk.core.exceptions import ParserException


class SignatureResult(binwalk.core.module.Result):

    '''
    Container class for signature results.
    '''

    def __init__(self, **kwargs):
        # These are set by signature keyword tags.
        # Keyword tags can also set any other object attributes,
        # including those in binwalk.core.module.Result.
        self.jump = 0
        self.many = False
        self.adjust = 0
        self.strlen = 0
        self.string = False
        self.invalid = False
        self.once = False
        self.overlap = False
        self.end = False

        # These are set by code internally
        self.id = 0

        # Kwargs overrides the defaults set above
        super(self.__class__, self).__init__(**kwargs)

        self.valid = (not self.invalid)


class SignatureLine(object):

    '''
    Responsible for parsing signature lines from magic signature files.
    '''

    # Printed strings are truncated to this size
    MAX_STRING_SIZE = 128

    def __init__(self, line):
        '''
        Class constructor. Responsible for parsing a line from a signature file.

        @line - A line of text from the signature file.

        Returns None.
        '''
        self.tags = {}
        self.text = line
        self.regex = False

        # Split the line on any white space; for this to work, backslash-escaped
        # spaces ('\ ') are replaced with their escaped hex value ('\x20').
        #
        # [offset] [data type] [comparison value] [format string]
        # 0        belong      0x12345678         Foo file type,
        # >4       string      x                  file name: %s,
        parts = line.replace('\\ ', '\\x20').split(None, 3)

        # Sanity check on the split line
        if len(parts) not in [3, 4]:
            raise ParserException("Invalid signature line: '%s'" % line)

        # The indentation level is determined by the number of '>' characters at
        # the beginning of the signature line.
        self.level = parts[0].count('>')

        # Get rid of the indentation characters and try to convert the remaining
        # characters to an integer offset. This will fail if the offset is a complex
        # value (e.g., '(4.l+16)').
        self.offset = parts[0].replace('>', '')
        try:
            self.offset = int(self.offset, 0)
        except ValueError as e:
            pass

        # self.type is the specified data type ('belong', 'string', etc)
        self.type = parts[1]
        self.opvalue = None
        self.operator = None

        # Each data type can specify an additional operation to be performed on the
        # data being scanned before performing a comparison (e.g., 'belong&0xFF' will
        # AND the data with 0xFF before the comparison is performed).
        #
        # We support the following operators:
        for operator in ['&', '|', '*', '+', '-', '/', '~', '^']:
            # Look for each operator in self.type
            if operator in self.type:
                # If found, split self.type into the type and operator value
                (self.type, self.opvalue) = self.type.split(operator, 1)

                # Keep a record of the specified operator
                self.operator = operator

                # Try to convert the operator value into an integer. This works for
                # simple operator values, but not for complex types (e.g.,
                # '(4.l+12)').
                try:
                    self.opvalue = int(self.opvalue, 0)
                except ValueError as e:
                    pass

                # Only one operator type is supported, so break as soon as one
                # is found
                break

        # If the specified type starts with 'u' (e.g., 'ubelong'), then it is
        # unsigned; else, it is signed
        if self.type[0] == 'u':
            self.signed = False
            self.type = self.type[1:]
        else:
            self.signed = True

        # Big endian values start with 'be' ('belong'), little endian values start with 'le' ('lelong').
        # The struct module uses '>' to denote big endian and '<' to denote
        # little endian.
        if self.type.startswith('be'):
            self.type = self.type[2:]
            self.endianness = '>'
        elif self.type.startswith('le'):
            self.endianness = '<'
            self.type = self.type[2:]
        # Assume big endian if no endianness was explicitly specified
        else:
            self.endianness = '>'

        # Check the comparison value for the type of comparison to be performed (e.g.,
        # '=0x1234', '>0x1234', etc). If no operator is specified, '=' is implied.
        if parts[2][0] in ['=', '!', '>', '<', '&', '|', '^', '~']:
            self.condition = parts[2][0]
            self.value = parts[2][1:]
        else:
            self.condition = '='
            self.value = parts[2]

        # If this is a wildcard value, explicitly set self.value to None
        if self.value == 'x':
            self.value = None
        # String values need to be decoded, as they may contain escape
        # characters (e.g., '\x20')
        elif self.type == 'string':
            # String types support multiplication to easily match large
            # repeating byte sequences
            if '*' in self.value:
                try:
                    p = self.value.split('*')
                    self.value = p[0]
                    for n in p[1:]:
                        self.value *= int(n, 0)
                except KeyboardInterrupt as e:
                    raise e
                except Exception as e:
                    raise ParserException("Failed to expand string '%s' with integer '%s' in line '%s'" % (self.value, n, line))
            try:
                self.value = binwalk.core.compat.string_decode(self.value)
            except ValueError as e:
                raise ParserException("Failed to decode string value '%s' in line '%s'" % (self.value, line))
        # If a regex was specified, compile it
        elif self.type == 'regex':
            self.regex = True

            try:
                self.value = re.compile(self.value)
            except KeyboardInterrupt as e:
                raise e
            except Exception as e:
                raise ParserException("Invalid regular expression '%s': %s" % (self.value, str(e)))
        # Non-string types are integer values
        else:
            try:
                self.value = int(self.value, 0)
            except ValueError as e:
                raise ParserException("Failed to convert value '%s' to an integer on line '%s'" % (self.value, line))

        # Sanity check to make sure the first line of a signature has an
        # explicit value
        if self.level == 0 and self.value is None:
            raise ParserException("First element of a signature must specify a non-wildcard value: '%s'" % (line))

        # Set the size and struct format value for the specified data type.
        # This must be done, obviously, after the value has been parsed out
        # above.
        if self.type == 'string':
            # Strings don't have a struct format value, since they don't have
            # to be unpacked
            self.fmt = None

            # If a string type has a specific value, set the comparison size to
            # the length of that string
            if self.value:
                self.size = len(self.value)
            # Else, truncate the string to self.MAX_STRING_SIZE
            else:
                self.size = self.MAX_STRING_SIZE
        elif self.type == 'regex':
            # Regular expressions don't have a struct format value, since they
            # don't have to be unpacked
            self.fmt = None
            # The size of a matching regex is unknown until it is applied to
            # some data
            self.size = self.MAX_STRING_SIZE
        elif self.type == 'byte':
            self.fmt = 'b'
            self.size = 1
        elif self.type == 'short':
            self.fmt = 'h'
            self.size = 2
        elif self.type == 'quad':
            self.fmt = 'q'
            self.size = 8
        # Assume 4 byte length for all other supported data types
        elif self.type in ['long', 'date']:
            self.fmt = 'i'
            self.size = 4
        else:
            raise ParserException("Unknown data type '%s' in line '%s'" % (self.type, line))

        # The struct module uses the same characters for specifying signed and unsigned data types,
        # except that signed data types are upper case. The above if-else code sets self.fmt to the
        # lower case (unsigned) values.
        if not self.signed:
            self.fmt = self.fmt.upper()

        # If a struct format was identified, create a format string to be passed to struct.unpack
        # which specifies the endianness and data type format.
        if self.fmt:
            self.pkfmt = '%c%c' % (self.endianness, self.fmt)
        else:
            self.pkfmt = None

        # Check if a format string was specified (this is optional)
        if len(parts) == 4:
            # %lld formats are only supported if Python was built with HAVE_LONG_LONG
            self.format = parts[3].replace('%ll', '%l')

            # Regex to parse out tags, which are contained within curly braces
            retag = re.compile(r'\{.*?\}')

            # Parse out tag keywords from the format string
            for match in retag.finditer(self.format):
                # Get rid of the curly braces.
                tag = match.group().replace('{', '').replace('}', '')

                # If the tag specifies a value, it will be colon delimited
                # (e.g., '{name:%s}')
                if ':' in tag:
                    (n, v) = tag.split(':', 1)
                else:
                    n = tag
                    v = True

                # Create a new SignatureTag instance and append it to self.tags
                self.tags[n] = v

            # Remove all tags from the printable format string
            self.format = retag.sub('', self.format).strip()
        else:
            self.format = ""


class Signature(object):

    '''
    Class to hold signature data and generate signature regular expressions.
    '''

    def __init__(self, sid, first_line):
        '''
        Class constructor.

        @sid        - A ID value to uniquely identify this signature.
        @first_line - The first SignatureLine of the signature (subsequent
                      SignatureLines should be added via self.append).

        Returns None.
        '''
        self.id = sid
        self.lines = [first_line]
        self.title = first_line.format
        self.offset = first_line.offset
        self.regex = self._generate_regex(first_line)
        try:
            self.confidence = first_line.tags['confidence']
        except KeyError:
            self.confidence = first_line.size

    def _generate_regex(self, line):
        '''
        Generates a regular expression from the magic bytes of a signature.
        The regex is used by Magic._analyze.

        @line - The first SignatureLine object of the signature.

        Returns a compile regular expression.
        '''
        restr = ""

        # Strings and single byte signatures are taken at face value;
        # multi-byte integer values are turned into regex strings based
        # on their data type size and endianness.
        if line.type == 'regex':
            # Regex types are already compiled expressions.
            # Note that since re.finditer is used, unless the specified
            # regex accounts for it, overlapping signatures will be ignored.
            return line.value
        if line.type == 'string':
            restr = line.value
        elif line.size == 1:
            restr = chr(line.value)
        elif line.size == 2:
            if line.endianness == '<':
                restr = chr(line.value & 0xFF) + chr(line.value >> 8)
            elif line.endianness == '>':
                restr = chr(line.value >> 8) + chr(line.value & 0xFF)
        elif line.size == 4:
            if line.endianness == '<':
                restr = (chr(line.value & 0xFF) +
                         chr((line.value >> 8) & 0xFF) +
                         chr((line.value >> 16) & 0xFF) +
                         chr(line.value >> 24))
            elif line.endianness == '>':
                restr = (chr(line.value >> 24) +
                         chr((line.value >> 16) & 0xFF) +
                         chr((line.value >> 8) & 0xFF) +
                         chr(line.value & 0xFF))
        elif line.size == 8:
            if line.endianness == '<':
                restr = (chr(line.value & 0xFF) +
                         chr((line.value >> 8) & 0xFF) +
                         chr((line.value >> 16) & 0xFF) +
                         chr((line.value >> 24) & 0xFF) +
                         chr((line.value >> 32) & 0xFF) +
                         chr((line.value >> 40) & 0xFF) +
                         chr((line.value >> 48) & 0xFF) +
                         chr(line.value >> 56))
            elif line.endianness == '>':
                restr = (chr(line.value >> 56) +
                         chr((line.value >> 48) & 0xFF) +
                         chr((line.value >> 40) & 0xFF) +
                         chr((line.value >> 32) & 0xFF) +
                         chr((line.value >> 24) & 0xFF) +
                         chr((line.value >> 16) & 0xFF) +
                         chr((line.value >> 8) & 0xFF) +
                         chr(line.value & 0xFF))

        # Since re.finditer is used on a per-signature basis, signatures should be crafted carefully
        # to ensure that they aren't potentially self-overlapping (e.g., a signature of "ABCDAB" could
        # be confused by the byte sequence "ABCDABCDAB"). The longer the signature, the less likely an
        # unintentional overlap is, although files could still be maliciously crafted to cause false
        # negative results.
        #
        # Thus, unless a signature has been explicitly marked as knowingly overlapping ('{overlap}'),
        # spit out a warning about any self-overlapping signatures.
        if not binwalk.core.compat.has_key(line.tags, 'overlap'):
            for i in range(1, line.size):
                if restr[i:] == restr[0:(line.size - i)]:
                    binwalk.core.common.warning("Signature '%s' is a self-overlapping signature!" % line.text)
                    break

        return re.compile(re.escape(restr))

    def append(self, line):
        '''
        Add a new SignatureLine object to the signature.

        @line - A new SignatureLine instance.

        Returns None.
        '''
        # This method is kind of useless, but may be a nice wrapper for future
        # code.
        self.lines.append(line)


class Magic(object):

    '''
    Primary class for loading signature files and scanning
    blocks of arbitrary data for matching signatures.
    '''

    def __init__(self, exclude=[], include=[], invalid=False):
        '''
        Class constructor.

        @include - A list of regex strings describing which signatures should be included in the scan results.
        @exclude - A list of regex strings describing which signatures should not be included in the scan results.
        @invalid - If set to True, invalid results will not be ignored.

        Returns None.
        '''
        # Used to save the block of data passed to self.scan (see additional
        # comments in self.scan)
        self.data = ""
        # A list of Signature class objects, populated by self.parse (see also:
        # self.load)
        self.signatures = []
        # A set of signatures with the 'once' keyword that have already been
        # displayed once
        self.display_once = set()
        self.dirty = True

        self.show_invalid = invalid
        self.includes = [re.compile(x) for x in include]
        self.excludes = [re.compile(x) for x in exclude]

        # Regex rule to replace backspace characters (an the preceeding character)
        # in formatted signature strings (see self._analyze).
        self.bspace = re.compile(".\\\\b")
        # Regex rule to match printable ASCII characters in formatted signature
        # strings (see self._analyze).
        self.printable = re.compile("[ -~]*")
        # Regex rule to find format strings
        self.fmtstr = re.compile("%[^%]")
        # Regex rule to find periods (see self._do_math)
        self.period = re.compile("\.")

    def reset(self):
        self.display_once = set()

    def _filtered(self, text):
        '''
        Tests if a string should be filtered out or not.

        @text - The string to check against filter rules.

        Returns True if the string should be filtered out, i.e., not displayed.
        Returns False if the string should be displayed.
        '''
        filtered = None
        # Text is converted to lower case first, partially for historical
        # purposes, but also because it simplifies writing filter rules
        # (e.g., don't have to worry about case sensitivity).
        text = text.lower()

        for include in self.includes:
            if include.search(text):
                filtered = False
                break

        # If exclusive include filters have been specified and did
        # not match the text, then the text should be filtered out.
        if self.includes and filtered == None:
            return True

        for exclude in self.excludes:
            if exclude.search(text):
                filtered = True
                break

        # If no explicit exclude filters were matched, then the
        # text should *not* be filtered.
        if filtered == None:
            filtered = False

        return filtered

    def _do_math(self, offset, expression):
        '''
        Parses and evaluates complex expressions, e.g., "(4.l+12)", "(6*32)", etc.

        @offset      - The offset inside self.data that the current signature starts at.
        @expressions - The expression to evaluate.

        Returns an integer value that is the result of the evaluated expression.
        '''
        # Does the expression contain an offset (e.g., "(4.l+12)")?
        if '.' in expression and '(' in expression:
            replacements = {}

            for period in [match.start() for match in self.period.finditer(expression)]:
                # Separate the offset field into the integer offset and type
                # values (o and t respsectively)
                s = expression[:period].rfind('(') + 1
                # The offset address may be an evaluatable expression, such as '(4+0.L)', typically the result
                # of the original offset being something like '(&0.L)'.
                o = binwalk.core.common.MathExpression(expression[s:period]).value
                t = expression[period + 1]

                # Re-build just the parsed offset portion of the expression
                text = "%s.%c" % (expression[s:period], t)

                # Have we already evaluated this offset expression? If so, skip
                # it.
                if binwalk.core.common.has_key(replacements, text):
                    continue

                # The offset specified in the expression is relative to the
                # starting offset inside self.data
                o += offset

                # Read the value from self.data at the specified offset
                try:
                    # Big and little endian byte format
                    if t in ['b', 'B']:
                        v = struct.unpack('b', binwalk.core.compat.str2bytes(self.data[o:o + 1]))[0]
                    # Little endian short format
                    elif t == 's':
                        v = struct.unpack('<h', binwalk.core.compat.str2bytes(self.data[o:o + 2]))[0]
                    # Little endian long format
                    elif t == 'l':
                        v = struct.unpack('<i', binwalk.core.compat.str2bytes(self.data[o:o + 4]))[0]
                    # Big endian short format
                    elif t == 'S':
                        v = struct.unpack('>h', binwalk.core.compat.str2bytes(self.data[o:o + 2]))[0]
                    # Bit endian long format
                    elif t == 'L':
                        v = struct.unpack('>i', binwalk.core.compat.str2bytes(self.data[o:o + 4]))[0]
                # struct.error is thrown if there is not enough bytes in
                # self.data for the specified format type
                except struct.error as e:
                    v = 0

                # Keep track of all the recovered values from self.data
                replacements[text] = v

            # Finally, replace all offset expressions with their corresponding
            # text value
            v = expression
            for (text, value) in binwalk.core.common.iterator(replacements):
                v = v.replace(text, "%d" % value)

        # If no offset, then it's just an evaluatable math expression (e.g.,
        # "(32+0x20)")
        else:
            v = expression

        # Evaluate the final expression
        value = binwalk.core.common.MathExpression(v).value

        return value

    def _analyze(self, signature, offset):
        '''
        Analyzes self.data for the specified signature data at the specified offset .

        @signature - The signature to apply to the data.
        @offset    - The offset in self.data to apply the signature to.

        Returns a dictionary of tags parsed from the data.
        '''
        description = []
        max_line_level = 0
        previous_line_end = 0
        tags = {'id': signature.id, 'offset':
                offset, 'invalid': False, 'once': False}

        # Apply each line of the signature to self.data, starting at the
        # specified offset
        for n in range(0, len(signature.lines)):
            line = signature.lines[n]

            # Ignore indentation levels above the current max indent level
            if line.level <= max_line_level:
                # If the relative offset of this signature line is just an
                # integer value, use it
                if isinstance(line.offset, int):
                    line_offset = line.offset
                # Else, evaluate the complex expression
                else:
                    # Format the previous_line_end value into a string. Add the '+' sign to explicitly
                    # state that this value is to be added to any subsequent values in the expression
                    # (e.g., '&0' becomes '4+0').
                    ple = '%d+' % previous_line_end
                    # Allow users to use either the '&0' (libmagic) or '&+0' (explcit addition) sytaxes;
                    # replace both with the ple text.
                    line_offset_text = line.offset.replace('&+', ple).replace('&', ple)
                    # Evaluate the expression
                    line_offset = self._do_math(offset, line_offset_text)

                # Sanity check
                if not isinstance(line_offset, int):
                    raise ParserException("Failed to convert offset '%s' to a number: '%s'" % (line.offset, line.text))

                # The start of the data needed by this line is at offset + line_offset.
                # The end of the data will be line.size bytes later.
                start = offset + line_offset
                end = start + line.size

                # If the line has a packed format string, unpack it
                if line.pkfmt:
                    try:
                        dvalue = struct.unpack(line.pkfmt, binwalk.core.compat.str2bytes(self.data[start:end]))[0]
                    # Not enough bytes left in self.data for the specified
                    # format size
                    except struct.error as e:
                        dvalue = 0
                # Else, this is a string
                else:
                    # Wildcard strings have line.value == None
                    if line.value is None:
                        # Check to see if this is a string whose size is known and has been specified on a previous
                        # signature line.
                        if binwalk.core.compat.has_key(tags, 'strlen') and binwalk.core.compat.has_key(line.tags, 'string'):
                            dvalue = self.data[start:(start + tags['strlen'])]
                        # Else, just terminate the string at the first newline,
                        # carriage return, or NULL byte
                        else:
                            dvalue = self.data[start:end].split('\x00')[0].split('\r')[0].split('\n')[0]
                    # Non-wildcard strings have a known length, specified in
                    # the signature line
                    else:
                        dvalue = self.data[start:end]

                # Some integer values have special operations that need to be performed on them
                # before comparison (e.g., "belong&0x0000FFFF"). Complex math expressions are
                # supported here as well.
                # if isinstance(dvalue, int) and line.operator:
                if line.operator:
                    try:
                        # If the operator value of this signature line is just
                        # an integer value, use it
                        if isinstance(line.opvalue, int) or isinstance(line.opvalue, long):
                            opval = line.opvalue
                        # Else, evaluate the complex expression
                        else:
                            opval = self._do_math(offset, line.opvalue)

                        # Perform the specified operation
                        if line.operator == '&':
                            dvalue &= opval
                        elif line.operator == '|':
                            dvalue |= opval
                        elif line.operator == '*':
                            dvalue *= opval
                        elif line.operator == '+':
                            dvalue += opval
                        elif line.operator == '-':
                            dvalue -= opval
                        elif line.operator == '/':
                            dvalue /= opval
                        elif line.operator == '~':
                            dvalue = ~opval
                        elif line.operator == '^':
                            dvalue ^= opval
                    except KeyboardInterrupt as e:
                        raise e
                    except Exception as e:
                        raise ParserException("Operation '" +
                                              str(dvalue) +
                                              " " +
                                              str(line.operator) +
                                              "= " +
                                              str(line.opvalue) +
                                              "' failed: " + str(e))

                # Does the data (dvalue) match the specified comparison?
                if ((line.value is None) or
                    (line.regex and line.value.match(dvalue)) or
                    (line.condition == '=' and dvalue == line.value) or
                    (line.condition == '>' and dvalue > line.value) or
                    (line.condition == '<' and dvalue < line.value) or
                    (line.condition == '!' and dvalue != line.value) or
                    (line.condition == '~' and (dvalue == ~line.value)) or
                    (line.condition == '^' and (dvalue ^ line.value)) or
                    (line.condition == '&' and (dvalue & line.value)) or
                        (line.condition == '|' and (dvalue | line.value))):

                    # Up until this point, date fields are treated as integer values,
                    # but we want to display them as nicely formatted strings.
                    if line.type == 'date':
                        try:
                            ts = datetime.datetime.utcfromtimestamp(dvalue)
                            dvalue = ts.strftime("%Y-%m-%d %H:%M:%S")
                        except KeyboardInterrupt as e:
                            raise e
                        except Exception:
                            dvalue = "invalid timestamp"

                    # Generate the tuple for the format string
                    dvalue_tuple = ()
                    for x in self.fmtstr.finditer(line.format):
                        dvalue_tuple += (dvalue,)

                    # Format the description string
                    desc = line.format % dvalue_tuple

                    # If there was any description string, append it to the
                    # list of description string parts
                    if desc:
                        description.append(desc)

                    # Process tag keywords specified in the signature line. These have already been parsed out of the
                    # original format string so that they can be processed
                    # separately from the printed description string.
                    for (tag_name, tag_value) in binwalk.core.compat.iterator(line.tags):
                        # If the tag value is a string, try to format it
                        if isinstance(tag_value, str):
                            # Generate the tuple for the format string
                            dvalue_tuple = ()
                            for x in self.fmtstr.finditer(tag_value):
                                dvalue_tuple += (dvalue,)

                            # Format the tag string
                            tags[tag_name] = tag_value % dvalue_tuple
                        # Else, just use the raw tag value
                        else:
                            tags[tag_name] = tag_value

                        # Some tag values are intended to be integer values, so
                        # try to convert them as such
                        try:
                            tags[tag_name] = int(tags[tag_name], 0)
                        except KeyboardInterrupt as e:
                            raise e
                        except Exception as e:
                            pass

                    # Abort processing soon as this signature is marked invalid, unless invalid results
                    # were explicitly requested. This means that the sooner invalid checks are made in a
                    # given signature, the faster the scan can filter out false
                    # positives.
                    if not self.show_invalid and tags['invalid']:
                        break

                    # Look ahead to the next line in the signature; if its indent level is greater than
                    # that of the current line, then track the end of data for the current line. This is
                    # so that subsequent lines can use the '>>&0' offset syntax to specify relative offsets
                    # from previous lines.
                    try:
                        next_line = signature.lines[n + 1]
                        if next_line.level > line.level:
                            if line.type == 'string':
                                previous_line_end = line_offset + len(dvalue)
                            else:
                                previous_line_end = line_offset + line.size
                    except IndexError as e:
                        pass

                    # If this line satisfied its comparison, +1 the max
                    # indentation level
                    max_line_level = line.level + 1
                else:
                    # No match on the first line, abort
                    if line.level == 0:
                        break
                    else:
                        # If this line did not satisfy its comparison, then higher
                        # indentation levels will not be accepted.
                        max_line_level = line.level

        # Join the formatted description strings and remove backspace
        # characters (plus the preceeding character as well)
        tags['description'] = self.bspace.sub('', " ".join(description))

        # This should never happen
        if not tags['description']:
            tags['display'] = False
            tags['invalid'] = True

        # If the formatted string contains non-printable characters, consider
        # it invalid
        if self.printable.match(tags['description']).group() != tags['description']:
            tags['invalid'] = True

        return tags

    def match(self, data):
        '''
        Match the beginning of a data buffer to a signature.

        @data - The data buffer to match against the loaded signature list.

        Returns a list of SignatureResult objects.
        '''
        return self.scan(data, 1)

    def scan(self, data, dlen=None):
        '''
        Scan a data block for matching signatures.

        @data - A string of data to scan.
        @dlen - If specified, signatures at offsets larger than dlen will be ignored.

        Returns a list of SignatureResult objects.
        '''
        results = []
        matched_offsets = set()

        # Since data can potentially be quite a large string, make it available to other
        # methods via a class attribute so that it doesn't need to be passed around to
        # different methods over and over again.
        self.data = data

        # If dlen wasn't specified, search all of self.data
        if dlen is None:
            dlen = len(data)

        sc = 0
        for signature in self.signatures:
            # Use regex to search the data block for potential signature
            # matches (fast)
            sc += 1
            for match in signature.regex.finditer(data):
                # Take the offset of the start of the signature into account
                offset = match.start() - signature.offset

                # Signatures are ordered based on the length of their magic bytes (largest first).
                # If this offset has already been matched to a previous signature, ignore it unless
                # self.show_invalid has been specified. Also ignore obviously invalid offsets (<0)
                # as well as those outside the specified self.data range (dlen).
                if (offset not in matched_offsets or self.show_invalid) and offset >= 0 and offset < dlen:
                # if offset >= 0 and offset < dlen:
                    # Analyze the data at this offset using the current
                    # signature rule
                    tags = self._analyze(signature, offset)

                    # Generate a SignatureResult object and append it to the results list if the
                    # signature is valid, or if invalid results were requested.
                    if (not tags['invalid'] or self.show_invalid) and not self._filtered(tags['description']):
                        # Only display results with the 'once' tag once.
                        if tags['once']:
                            if signature.title in self.display_once:
                                continue
                            else:
                                self.display_once.add(signature.title)
                        
                        # Append the result to the results list
                        results.append(SignatureResult(**tags))

                        # Add this offset to the matched_offsets set, so that it can be ignored by
                        # subsequent loops.
                        matched_offsets.add(offset)

        # Sort results by offset
        results.sort(key=lambda x: x.offset, reverse=False)

        return results

    def load(self, fname):
        '''
        Load signatures from a file.

        @fname - Path to signature file.

        Returns None.
        '''
        # Magic files must be ASCII, else encoding issues can arise.
        fp = open(fname, "r")
        lines = fp.readlines()
        self.parse(lines)
        fp.close()

    def parse(self, lines):
        '''
        Parse signature file lines.

        @lines - A list of lines from a signature file.

        Returns None.
        '''
        signature = None

        for line in lines:
            # Split at the first comment delimiter (if any) and strip the
            # result
            line = line.split('#')[0].strip()
            # Ignore blank lines and lines that are nothing but comments.
            # We also don't support the '!mime' style line entries.
            if line and line[0] != '!':
                # Parse this signature line
                sigline = SignatureLine(line)
                # Level 0 means the first line of a signature entry
                if sigline.level == 0:
                    # If there is an existing signature, append it to the signature list,
                    # unless the text in its title field has been filtered by user-defined
                    # filter rules.
                    if signature and not self._filtered(signature.title):
                        self.signatures.append(signature)

                    # Create a new signature object; use the size of self.signatures to
                    # assign each signature a unique ID.
                    signature = Signature(len(self.signatures), sigline)
                # Else, just append this line to the existing signature
                elif signature:
                    # signature.append(sigline)
                    signature.lines.append(sigline)
                # If this is not the first line of a signature entry and there is no other
                # existing signature entry, something is very wrong with the
                # signature file.
                else:
                    raise ParserException("Invalid signature line: '%s'" % line)

        # Add the final signature to the signature list
        if signature:
            if not self._filtered(signature.lines[0].format):
                self.signatures.append(signature)

        # Sort signatures by confidence (aka, length of their magic bytes),
        # largest first
        self.signatures.sort(key=lambda x: x.confidence, reverse=True)
