# Common functions used throughout various parts of binwalk code.

import io
import os
import re
import sys
import ast
import platform
import operator as op
import binwalk.core.idb
from binwalk.core.compat import *

# Don't try to import hashlib when loaded into IDA; it doesn't work.
if not binwalk.core.idb.LOADED_IN_IDA:
    import hashlib

# The __debug__ value is a bit backwards; by default it is set to True, but
# then set to False if the Python interpreter is run with the -O option.
if not __debug__:
    DEBUG = True
else:
    DEBUG = False


def MSWindows():
    # Returns True if running in a Microsoft Windows OS
    return (platform.system() == 'Windows')


def debug(msg):
    '''
    Displays debug messages to stderr only if the Python interpreter was invoked with the -O flag.
    '''
    if DEBUG:
        sys.stderr.write("DEBUG: " + msg + "\n")
        sys.stderr.flush()


def warning(msg):
    '''
    Prints warning messages to stderr
    '''
    sys.stderr.write("\nWARNING: " + msg + "\n")


def error(msg):
    '''
    Prints error messages to stderr
    '''
    sys.stderr.write("\nERROR: " + msg + "\n")


def critical(msg):
    '''
    Prints critical messages to stderr
    '''
    sys.stderr.write("\nCRITICAL: " + msg + "\n")


def get_module_path():
    root = __file__
    if os.path.islink(root):
        root = os.path.realpath(root)
    return os.path.dirname(os.path.dirname(os.path.abspath(root)))


def get_libs_path():
    return os.path.join(get_module_path(), "libs")


def file_md5(file_name):
    '''
    Generate an MD5 hash of the specified file.

    @file_name - The file to hash.

    Returns an MD5 hex digest string.
    '''
    md5 = hashlib.md5()

    with open(file_name, 'rb') as f:
        for chunk in iter(lambda: f.read(128 * md5.block_size), b''):
            md5.update(chunk)

    return md5.hexdigest()


def file_size(filename):
    '''
    Obtains the size of a given file.

    @filename - Path to the file.

    Returns the size of the file.
    '''
    # Using open/lseek works on both regular files and block devices
    fd = os.open(filename, os.O_RDONLY)
    try:
        return os.lseek(fd, 0, os.SEEK_END)
    except KeyboardInterrupt as e:
        raise e
    except Exception as e:
        raise Exception(
            "file_size failed to obtain the size of '%s': %s" % (filename, str(e)))
    finally:
        os.close(fd)


def strip_quoted_strings(quoted_string):
    '''
    Strips out data in between double quotes.

    @quoted_string - String to strip.

    Returns a sanitized string.
    '''
    # This regex removes all quoted data from string.
    # Note that this removes everything in between the first and last double quote.
    # This is intentional, as printed (and quoted) strings from a target file may contain
    # double quotes, and this function should ignore those. However, it also means that any
    # data between two quoted strings (ex: '"quote 1" you won't see me "quote
    # 2"') will also be stripped.
    return re.sub(r'\"(.*)\"', "", quoted_string)


def get_quoted_strings(quoted_string):
    '''
    Returns a string comprised of all data in between double quotes.

    @quoted_string - String to get quoted data from.

    Returns a string of quoted data on success.
    Returns a blank string if no quoted data is present.
    '''
    try:
        # This regex grabs all quoted data from string.
        # Note that this gets everything in between the first and last double quote.
        # This is intentional, as printed (and quoted) strings from a target file may contain
        # double quotes, and this function should ignore those. However, it also means that any
        # data between two quoted strings (ex: '"quote 1" non-quoted data
        # "quote 2"') will also be included.
        return re.findall(r'\"(.*)\"', quoted_string)[0]
    except KeyboardInterrupt as e:
        raise e
    except Exception:
        return ''


def unique_file_name(base_name, extension=''):
    '''
    Creates a unique file name based on the specified base name.

    @base_name - The base name to use for the unique file name.
    @extension - The file extension to use for the unique file name.

    Returns a unique file string.
    '''
    idcount = 0

    if extension and not extension.startswith('.'):
        extension = '.%s' % extension

    fname = base_name + extension

    while os.path.exists(fname):
        fname = "%s-%d%s" % (base_name, idcount, extension)
        idcount += 1

    return fname


def strings(filename, minimum=4):
    '''
    A strings generator, similar to the Unix strings utility.

    @filename - The file to search for strings in.
    @minimum  - The minimum string length to search for.

    Yeilds printable ASCII strings from filename.
    '''
    result = ""

    with BlockFile(filename) as f:
        while True:
            (data, dlen) = f.read_block()
            if dlen < 1:
                break

            for c in data:
                if c in string.printable:
                    result += c
                    continue
                elif len(result) >= minimum:
                    yield result
                    result = ""
                else:
                    result = ""


class GenericContainer(object):

    def __init__(self, **kwargs):
        for (k, v) in iterator(kwargs):
            setattr(self, k, v)


class MathExpression(object):

    '''
    Class for safely evaluating mathematical expressions from a string.
    Stolen from: http://stackoverflow.com/questions/2371436/evaluating-a-mathematical-expression-in-a-string
    '''

    OPERATORS = {
        ast.Add:    op.add,
        ast.UAdd:   op.add,
        ast.USub:   op.sub,
        ast.Sub:    op.sub,
        ast.Mult:   op.mul,
        ast.Div:    op.truediv,
        ast.Pow:    op.pow,
        ast.BitXor: op.xor
    }

    def __init__(self, expression):
        self.expression = expression
        self.value = None

        if expression:
            try:
                self.value = self.evaluate(self.expression)
            except KeyboardInterrupt as e:
                raise e
            except Exception as e:
                pass

    def evaluate(self, expr):
        return self._eval(ast.parse(expr).body[0].value)

    def _eval(self, node):
        if isinstance(node, ast.Num):  # <number>
            return node.n
        elif isinstance(node, ast.operator):  # <operator>
            return self.OPERATORS[type(node.op)]
        elif isinstance(node, ast.UnaryOp):
            return self.OPERATORS[type(node.op)](0, self._eval(node.operand))
        elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
            return self.OPERATORS[type(node.op)](self._eval(node.left), self._eval(node.right))
        else:
            raise TypeError(node)


class StringFile(object):

    '''
    A class to allow access to strings as if they were read from a file.
    Used internally as a conditional superclass to InternalBlockFile.
    '''

    def __init__(self, fname, mode='r'):
        self.string = fname #bytes2str(fname)
        self.name = "String"
        self.args.size = len(self.string)

    def read(self, n=-1):
        if n == -1:
            data = self.string[self.total_read:]
        else:
            data = self.string[self.total_read:self.total_read + n]
        return data

    def tell(self):
        return self.total_read

    def write(self, *args, **kwargs):
        pass

    def seek(self, *args, **kwargs):
        pass

    def close(self):
        pass


def BlockFile(fname, mode='r', subclass=io.FileIO, **kwargs):

    # Defining a class inside a function allows it to be dynamically subclassed
    class InternalBlockFile(subclass):

        '''
        Abstraction class for accessing binary files.

        This class overrides io.FilIO's read and write methods. This guaruntees two things:

            1. All requested data will be read/written via the read and write methods.
            2. All reads return a str object and all writes can accept either a str or a
               bytes object, regardless of the Python interpreter version.

        However, the downside is that other io.FileIO methods won't work properly in Python 3,
        namely things that are wrappers around self.read (e.g., readline, readlines, etc).

        This class also provides a read_block method, which is used by binwalk to read in a
        block of data, plus some additional data (DEFAULT_BLOCK_PEEK_SIZE), but on the next block read
        pick up at the end of the previous data block (not the end of the additional data). This
        is necessary for scans where a signature may span a block boundary.

        The descision to force read to return a str object instead of a bytes object is questionable
        for Python 3, but it seemed the best way to abstract differences in Python 2/3 from the rest
        of the code (especially for people writing plugins) and to add Python 3 support with
        minimal code change.
        '''

        # The DEFAULT_BLOCK_PEEK_SIZE limits the amount of data available to a signature.
        # While most headers/signatures are far less than this value, some may reference
        # pointers in the header structure which may point well beyond the header itself.
        # Passing the entire remaining buffer to libmagic is resource intensive and will
        # significantly slow the scan; this value represents a reasonable buffer size to
        # pass to libmagic which will not drastically affect scan time.
        DEFAULT_BLOCK_PEEK_SIZE = 8 * 1024

        # Max number of bytes to process at one time. This needs to be large enough to
        # limit disk I/O, but small enough to limit the size of processed data
        # blocks.
        DEFAULT_BLOCK_READ_SIZE = 1 * 1024 * 1024

        def __init__(self, fname, mode='r', length=0, offset=0, block=DEFAULT_BLOCK_READ_SIZE, peek=DEFAULT_BLOCK_PEEK_SIZE, swap=0):
            '''
            Class constructor.

            @fname  - Path to the file to be opened.
            @mode   - Mode to open the file in (default: 'r').
            @length - Maximum number of bytes to read from the file via self.block_read().
            @offset - Offset at which to start reading from the file.
            @block  - Size of data block to read (excluding any trailing size),
            @peek   - Size of trailing data to append to the end of each block.
            @swap   - Swap every n bytes of data.

            Returns None.
            '''
            self.total_read = 0
            self.block_read_size = self.DEFAULT_BLOCK_READ_SIZE
            self.block_peek_size = self.DEFAULT_BLOCK_PEEK_SIZE

            # This is so that custom parent classes can access/modify arguments
            # as necessary
            self.args = GenericContainer(fname=fname,
                                         mode=mode,
                                         length=length,
                                         offset=offset,
                                         block=block,
                                         peek=peek,
                                         swap=swap,
                                         size=0)

            # Python 2.6 doesn't like modes like 'rb' or 'wb'
            mode = self.args.mode.replace('b', '')

            super(self.__class__, self).__init__(fname, mode)

            self.swap_size = self.args.swap

            if self.args.size:
                self.size = self.args.size
            else:
                try:
                    self.size = file_size(self.args.fname)
                except KeyboardInterrupt as e:
                    raise e
                except Exception:
                    self.size = 0

            if self.args.offset < 0:
                self.offset = self.size + self.args.offset
            else:
                self.offset = self.args.offset

            if self.offset < 0:
                self.offset = 0
            elif self.offset > self.size:
                self.offset = self.size

            if self.args.offset < 0:
                self.length = self.args.offset * -1
            elif self.args.length:
                self.length = self.args.length
            else:
                self.length = self.size - self.args.offset

            if self.length < 0:
                self.length = 0
            elif self.length > self.size:
                self.length = self.size

            if self.args.block is not None:
                self.block_read_size = self.args.block
            self.base_block_size = self.block_read_size

            if self.args.peek is not None:
                self.block_peek_size = self.args.peek
            self.base_peek_size = self.block_peek_size

            # Work around for python 2.6 where FileIO._name is not defined
            try:
                self.name
            except AttributeError:
                self._name = fname

            self.path = os.path.abspath(self.name)
            self.seek(self.offset)

        def _swap_data_block(self, block):
            '''
            Reverses every self.swap_size bytes inside the specified data block.
            Size of data block must be a multiple of self.swap_size.

            @block - The data block to swap.

            Returns a swapped string.
            '''
            i = 0
            data = ""

            if self.swap_size > 0:
                while i < len(block):
                    data += block[i:i + self.swap_size][::-1]
                    i += self.swap_size
            else:
                data = block

            return data

        def reset(self):
            self.set_block_size(
                block=self.base_block_size, peek=self.base_peek_size)
            self.seek(self.offset)

        def set_block_size(self, block=None, peek=None):
            if block is not None:
                self.block_read_size = block
            if peek is not None:
                self.block_peek_size = peek

        def write(self, data):
            '''
            Writes data to the opened file.

            io.FileIO.write does not guaruntee that all data will be written;
            this method overrides io.FileIO.write and does guaruntee that all data will be written.

            Returns the number of bytes written.
            '''
            n = 0
            l = len(data)
            data = str2bytes(data)

            while n < l:
                n += super(self.__class__, self).write(data[n:])

            return n

        def read(self, n=-1, override=False):
            ''''
            Reads up to n bytes of data (or to EOF if n is not specified).
            Will not read more than self.length bytes unless override == True.

            io.FileIO.read does not guaruntee that all requested data will be read;
            this method overrides io.FileIO.read and does guaruntee that all data will be read.

            Returns a str object containing the read data.
            '''
            l = 0
            data = b''

            if override == True or (self.total_read < self.length):
                # Don't read more than self.length bytes from the file
                # unless an override has been requested.
                if override == False and (self.total_read + n) > self.length:
                    n = self.length - self.total_read

                while n < 0 or l < n:
                    tmp = super(self.__class__, self).read(n - l)
                    if tmp:
                        data += tmp
                        l += len(tmp)
                    else:
                        break

                self.total_read += len(data)

            return self._swap_data_block(bytes2str(data))

        def peek(self, n=-1):
            '''
            Peeks at data in file.
            '''
            pos = self.tell()
            data = self.read(n, override=True)
            self.seek(pos)
            return data

        def seek(self, n, whence=os.SEEK_SET):
            if whence == os.SEEK_SET:
                self.total_read = n - self.offset
            elif whence == os.SEEK_CUR:
                self.total_read += n
            elif whence == os.SEEK_END:
                self.total_read = self.size + n

            super(self.__class__, self).seek(n, whence)

        def read_block(self):
            '''
            Reads in a block of data from the target file.

            Returns a tuple of (str(file block data), block data length).
            '''
            data = self.read(self.block_read_size)
            dlen = len(data)
            data += self.peek(self.block_peek_size)

            return (data, dlen)

    return InternalBlockFile(fname, mode=mode, **kwargs)
