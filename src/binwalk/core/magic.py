import re
import struct
import datetime
import binwalk.core.compat

class ParserException(Exception):
    pass

class SignatureTag(object):
    def __init__(self, **kwargs):
        for (k,v) in binwalk.core.compat.iterator(kwargs):
            setattr(self, k, v)

class SignatureResult(object):

    def __init__(self, **kwargs):
        # These are set by signature keyword tags
        self.jump = 0
        self.many = False
        self.size = 0
        self.name = None
        self.offset = 0
        self.strlen = 0
        self.string = False
        self.invalid = False
        self.extract = True

        # These are set by code internally
        self.id = 0
        self.file = None
        self.valid = True
        self.display = True
        self.description = ""

        for (k,v) in binwalk.core.compat.iterator(kwargs):
            setattr(self, k, v)

        self.valid = (not self.invalid)

class SignatureLine(object):

    def __init__(self, line):
        self.tags = []
        self.original_text = line

        parts = line.replace('\\ ', '\\x20').split(None, 3)

        self.level = parts[0].count('>')

        self.offset = parts[0].replace('>', '')
        try:
            self.offset = int(self.offset, 0)
        except ValueError as e:
            pass

        self.type = parts[1]
        self.opvalue = None
        self.operator = None
        for operator in ['&', '|', '*', '+', '-', '/']:
            if operator in parts[1]:
                (self.type, self.opvalue) = parts[1].split(operator, 1)
                self.operator = operator
                self.opvalue = int(self.opvalue, 0)
                break

        if parts[2][0] in ['=', '!', '>', '<', '&', '|']:
            self.condition = parts[2][0]
            self.value = parts[2][1:]
        else:
            self.condition = '='
            self.value = parts[2]

        if self.value == 'x':
            self.value = None
        elif self.type == 'string':
            try:
                self.value = binwalk.core.compat.string_decode(self.value)
            except ValueError as e:
                raise ParserException("Failed to decode string value '%s' in line '%s'" % (self.value, line))
        else:
            self.value = int(self.value, 0)

        if len(parts) == 4:
            self.format = parts[3].replace('%ll', '%l')
            retag = re.compile(r'\{.*?\}')

            # Parse out tag keywords from the format string
            for tag in [m.group() for m in retag.finditer(self.format)]:
                tag = tag.replace('{', '').replace('}', '')
                if ':' in tag:
                    (n, v) = tag.split(':', 1)
                else:
                    n = tag
                    v = True
                self.tags.append(SignatureTag(name=n, value=v))

            # Remove tags from the printable format string
            self.format = retag.sub('', self.format).strip()
        else:
            self.format = ""

        if self.type[0] == 'u':
            self.signed = False
            self.type = self.type[1:]
        else:
            self.signed = True

        if self.type.startswith('be'):
            self.type = self.type[2:]
            self.endianess = '>'
        elif self.type.startswith('le'):
            self.endianess = '<'
            self.type = self.type[2:]
        else:
            self.endianess = '<'

        if self.type == 'string':
            self.fmt = None
            if self.value:
                self.size = len(self.value)
            else:
                self.size = 128
        elif self.type == 'byte':
            self.fmt = 'b'
            self.size = 1
        elif self.type == 'short':
            self.fmt = 'h'
            self.size = 2
        elif self.type == 'quad':
            self.fmt = 'q'
            self.size = 8
        else:
            self.fmt = 'i'
            self.size = 4

        if self.fmt:
            self.pkfmt = '%c%c' % (self.endianess, self.fmt)
        else:
            self.pkfmt = None

        if not self.signed:
            self.fmt = self.fmt.upper()

class Signature(object):

    def __init__(self, id, first_line):
        self.id = id
        self.lines = [first_line]
        self.title = first_line.format
        self.offset = first_line.offset
        self.confidence = first_line.size
        self.regex = self.generate_regex(first_line)

    def generate_regex(self, line):
        restr = ""

        if line.type in ['string']:
            restr = re.escape(line.value)
        elif line.size == 1:
            restr = re.escape(chr(line.value))
        elif line.size == 2:
            if line.endianess == '<':
                restr = re.escape(chr(line.value & 0xFF) + chr(line.value >> 8))
            elif line.endianess == '>':
                restr = re.escape(chr(line.value >> 8) + chr(line.value & 0xFF))
        elif line.size == 4:
            if line.endianess == '<':
                restr = re.escape(chr(line.value & 0xFF) +
                                  chr((line.value >> 8) & 0xFF) +
                                  chr((line.value >> 16) & 0xFF) +
                                  chr(line.value >> 24))
            elif line.endianess == '>':
                restr = re.escape(chr(line.value >> 24) +
                                  chr((line.value >> 16) & 0xFF) +
                                  chr((line.value >> 8) & 0xFF) +
                                  chr(line.value & 0xFF))
        elif line.size == 8:
            if line.endianess == '<':
                restr = re.escape(chr(line.value & 0xFF) +
                                  chr((line.value >> 8) & 0xFF) +
                                  chr((line.value >> 16) & 0xFF) +
                                  chr((line.value >> 24) & 0xFF) +
                                  chr((line.value >> 32) & 0xFF) +
                                  chr((line.value >> 40) & 0xFF) +
                                  chr((line.value >> 48) & 0xFF) +
                                  chr(line.value >> 56))
            elif line.endianess == '>':
                restr = re.escape(chr(line.value >> 56) +
                                  chr((line.value >> 48) & 0xFF) +
                                  chr((line.value >> 40) & 0xFF) +
                                  chr((line.value >> 32) & 0xFF) +
                                  chr((line.value >> 24) & 0xFF) +
                                  chr((line.value >> 16) & 0xFF) +
                                  chr((line.value >> 8) & 0xFF) +
                                  chr(line.value & 0xFF))

        return re.compile(restr)

    def append(self, line):
        self.lines.append(line)

class Magic(object):

    def __init__(self, exclude=[], include=[], invalid=False):
        '''
        Class constructor.

        @invalid - If set to True, invalid results will not be ignored.

        Returns None.
        '''
        self.data = ""
        self.signatures = []

        self.show_invalid = invalid
        self.includes = [re.compile(x) for x in include]
        self.excludes = [re.compile(x) for x in exclude]

        self.bspace = re.compile(".\\\\b")
        self.printable = re.compile("[ -~]*")

    def filtered(self, text):
        filtered = None
        text = text.lower()

        for include in self.includes:
            if include.match(text):
                filtered = False
                break

        if self.includes and filtered == None:
            return True

        for exclude in self.excludes:
            if exclude.match(text):
                filtered = True
                break

        if filtered == None:
            filtered = False

        return filtered

    def parse(self, signature, offset):
        description = []
        tag_strlen = None
        max_line_level = 0
        tags = {'id' : signature.id, 'offset' : offset, 'invalid' : False}

        for line in signature.lines:
            if line.level <= max_line_level:
                if isinstance(line.offset, int):
                    line_offset = line.offset
                else:
                    # (4.l+12)
                    if '.' in line.offset:
                        (o, t) = line.offset.split('.', 1)
                        o = offset + int(o.split('(', 1)[1], 0)
                        t = t[0]

                        try:
                            if t in ['b', 'B']:
                                v = struct.unpack('b', binwalk.core.compat.str2bytes(self.data[o:o+1]))[0]
                            elif t == 's':
                                v = struct.unpack('<h', binwalk.core.compat.str2bytes(self.data[o:o+2]))[0]
                            elif t == 'l':
                                v = struct.unpack('<i', binwalk.core.compat.str2bytes(self.data[o:o+4]))[0]
                            elif t == 'S':
                                v = struct.unpack('>h', binwalk.core.compat.str2bytes(self.data[o:o+2]))[0]
                            elif t == 'L':
                                v = struct.unpack('>i', binwalk.core.compat.str2bytes(self.data[o:o+4]))[0]
                        except struct.error as e:
                            v = 0

                        v = "(%d%s" % (v, line.offset.split(t, 1)[1])
                    # (32+0x20)
                    else:
                        v = line.offset

                    #print ("Converted offset '%s' to '%s'" % (line.offset, v))
                    line_offset = binwalk.core.common.MathExpression(v).value

                start = offset + line_offset
                end = start + line.size

                if line.pkfmt:
                    try:
                        dvalue = struct.unpack(line.pkfmt, binwalk.core.compat.str2bytes(self.data[start:end]))[0]
                    except struct.error as e:
                        dvalue = 0
                else:
                    # Wildcard strings have line.value == None
                    if line.value is None:
                        if [x for x in line.tags if x.name == 'string'] and binwalk.core.compat.has_key(tags, 'strlen'):
                            dvalue = self.data[start:(start+tags['strlen'])]
                        else:
                            dvalue = self.data[start:end].split('\x00')[0].split('\r')[0].split('\r')[0]
                    else:
                        dvalue = self.data[start:end]

                if isinstance(dvalue, int) and line.operator:
                    if line.operator == '&':
                        dvalue &= line.opvalue
                    elif line.operator == '|':
                        dvalue |= line.opvalue
                    elif line.operator == '*':
                        dvalue *= line.opvalue
                    elif line.operator == '+':
                        dvalue += line.opvalue
                    elif line.operator == '-':
                        dvalue -= line.opvalue
                    elif line.operator == '/':
                        dvalue /= line.opvalue

                if ((line.value is None) or
                    (line.condition == '=' and dvalue == line.value) or
                    (line.condition == '>' and dvalue > line.value) or
                    (line.condition == '<' and dvalue < line.value) or
                    (line.condition == '!' and dvalue != line.value) or
                    (line.condition == '&' and (dvalue & line.value)) or
                    (line.condition == '|' and (dvalue | line.value))):

                    if line.type == 'date':
                        ts = datetime.datetime.utcfromtimestamp(dvalue)
                        dvalue = ts.strftime("%Y-%m-%d %H:%M:%S")

                    if '%' in line.format:
                        desc = line.format % dvalue
                    else:
                        desc = line.format

                    if desc:
                        description.append(desc)

                    for tag in line.tags:
                        if isinstance(tag.value, str) and '%' in tag.value:
                            tags[tag.name] = tag.value % dvalue
                            try:
                                tags[tag.name] = int(tags[tag.name], 0)
                            except KeyboardInterrupt as e:
                                raise e
                            except Exception as e:
                                pass
                        else:
                            try:
                                tags[tag.name] = int(tag.value, 0)
                            except KeyboardInterrupt as e:
                                raise e
                            except Exception as e:
                                tags[tag.name] = tag.value

                    # Abort abort abort
                    if not self.show_invalid and tags['invalid']:
                        break

                    max_line_level = line.level + 1
                else:
                    # No match on the first line, abort
                    if line.level == 0:
                        break
                    else:
                        max_line_level = line.level

        tags['description'] = self.bspace.sub('', " ".join(description))

        # This should never happen
        if not tags['description']:
            tags['display'] = False
            tags['invalid'] = True

        if self.printable.match(tags['description']).group() != tags['description']:
            tags['invalid'] = True

        return tags

    def scan(self, data, dlen=None):
        results = []
        matched_offsets = set()

        self.data = data
        if dlen is None:
            dlen = len(self.data)

        for signature in self.signatures:
            for match in signature.regex.finditer(self.data):
                offset = match.start() - signature.offset
                if (offset not in matched_offsets or self.show_invalid) and offset >= 0 and offset <= dlen:
                    tags = self.parse(signature, offset)
                    if not tags['invalid'] or self.show_invalid:
                        results.append(SignatureResult(**tags))
                        matched_offsets.add(offset)

        results.sort(key=lambda x: x.offset, reverse=False)
        return results

    def load(self, fname):
        '''
        Load signatures from a file.

        @fname - Path to signature file.

        Returns None.
        '''
        signature = None

        fp = open(fname, "r")

        for line in fp.readlines():
            line = line.split('#')[0].strip()
            if line:
                sigline = SignatureLine(line)
                if sigline.level == 0:
                    if signature:
                        if not self.filtered(signature.title):
                            self.signatures.append(signature)
                    signature = Signature(len(self.signatures), sigline)
                elif signature:
                    signature.append(sigline)
                else:
                    raise ParserException("Invalid signature line: '%s'" % line)

        if signature:
            if not self.filtered(signature.lines[0].format):
                self.signatures.append(signature)

        fp.close()

        self.signatures.sort(key=lambda x: x.confidence, reverse=True)

