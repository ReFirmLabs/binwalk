# Common functions.
import io
import os
import re
import ast
import hashlib
import operator as op
from binwalk.compat import *

def file_md5(file_name):
	'''
	Generate an MD5 hash of the specified file.
	
	@file_name - The file to hash.

	Returns an MD5 hex digest string.
	'''
	md5 = hashlib.md5()

	with open(file_name, 'rb') as f:
		for chunk in iter(lambda: f.read(128*md5.block_size), b''):
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
	except Exception as e:
		raise Exception("file_size failed to obtain the size of '%s': %s" % (filename, str(e)))
	finally:
		os.close(fd)

def str2int(string):
	'''
	Attempts to convert string to a base 10 integer; if that fails, then base 16.

	@string - String to convert to an integer.

	Returns the integer value on success.
	Throws an exception if the string cannot be converted into either a base 10 or base 16 integer value.
	'''
	try:
		return int(string)
	except:
		return int(string, 16)

def strip_quoted_strings(string):
	'''
	Strips out data in between double quotes.
	
	@string - String to strip.

	Returns a sanitized string.
	'''
	# This regex removes all quoted data from string.
	# Note that this removes everything in between the first and last double quote.
	# This is intentional, as printed (and quoted) strings from a target file may contain 
	# double quotes, and this function should ignore those. However, it also means that any 
	# data between two quoted strings (ex: '"quote 1" you won't see me "quote 2"') will also be stripped.
	return re.sub(r'\"(.*)\"', "", string)

def get_quoted_strings(string):
	'''
	Returns a string comprised of all data in between double quotes.

	@string - String to get quoted data from.

	Returns a string of quoted data on success.
	Returns a blank string if no quoted data is present.
	'''
	try:
		# This regex grabs all quoted data from string.
		# Note that this gets everything in between the first and last double quote.
		# This is intentional, as printed (and quoted) strings from a target file may contain 
		# double quotes, and this function should ignore those. However, it also means that any 
		# data between two quoted strings (ex: '"quote 1" non-quoted data "quote 2"') will also be included.
		return re.findall(r'\"(.*)\"', string)[0]
	except:
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
			if not data:
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

class MathExpression(object):
	'''
	Class for safely evaluating mathematical expressions from a string.
	Stolen from: http://stackoverflow.com/questions/2371436/evaluating-a-mathematical-expression-in-a-string
	'''

	OPERATORS = {
		ast.Add: op.add,
		ast.Sub: op.sub,
		ast.Mult: op.mul,
		ast.Div: op.truediv, 
		ast.Pow: op.pow, 
		ast.BitXor: op.xor
	}

	def __init__(self, expression):
		self.expression = expression
		self.value = None

		if expression:
			try:
				self.value = self.evaluate(self.expression)
			except:
				pass

	def evaluate(self, expr):
		return self._eval(ast.parse(expr).body[0].value)

	def _eval(self, node):
		if isinstance(node, ast.Num): # <number>
			return node.n
		elif isinstance(node, ast.operator): # <operator>
			return self.OPERATORS[type(node)]
		elif isinstance(node, ast.BinOp): # <left> <operator> <right>
			return self._eval(node.op)(self._eval(node.left), self._eval(node.right))
		else:
			raise TypeError(node)


class BlockFile(io.FileIO):
	'''
	Abstraction class for accessing binary files.

	This class overrides io.FilIO's read and write methods. This guaruntees two things:

		1. All requested data will be read/written via the read and write methods.
		2. All reads return a str object and all writes can accept either a str or a
		   bytes object, regardless of the Python interpreter version.

	However, the downside is that other io.FileIO methods won't work properly in Python 3,
	namely things that are wrappers around self.read (e.g., readline, readlines, etc).

	This class also provides a read_block method, which is used by binwalk to read in a
	block of data, plus some additional data (MAX_TRAILING_SIZE), but on the next block read
	pick up at the end of the previous data block (not the end of the additional data). This
	is necessary for scans where a signature may span a block boundary.

	The descision to force read to return a str object instead of a bytes object is questionable
	for Python 3, it seemed the best way to abstract differences in Python 2/3 from the rest
	of the code (especially for people writing plugins) and to add Python 3 support with 
	minimal code change.
	'''

	# The MAX_TRAILING_SIZE limits the amount of data available to a signature.
	# While most headers/signatures are far less than this value, some may reference 
	# pointers in the header structure which may point well beyond the header itself.
	# Passing the entire remaining buffer to libmagic is resource intensive and will
	# significantly slow the scan; this value represents a reasonable buffer size to
	# pass to libmagic which will not drastically affect scan time.
	MAX_TRAILING_SIZE = 8 * 1024

	# Max number of bytes to process at one time. This needs to be large enough to 
	# limit disk I/O, but small enough to limit the size of processed data blocks.
	READ_BLOCK_SIZE = 1 * 1024 * 1024

	def __init__(self, fname, mode='r', length=0, offset=0, block=READ_BLOCK_SIZE):
		'''
		Class constructor.

		@fname  - Path to the file to be opened.
		@mode   - Mode to open the file in (default: 'r').
		@length - Maximum number of bytes to read from the file via self.block_read().
		@offset - Offset at which to start reading from the file.

		Returns None.
		'''
		self.total_read = 0

		# Python 2.6 doesn't like modes like 'rb' or 'wb'
		mode = mode.replace('b', '')
		
		try:
			self.size = file_size(fname)
		except:
			self.size = 0

		if offset < 0:
			self.offset = self.size + offset
		else:
			self.offset = offset

		if self.offset < 0:
			self.offset = 0
		elif self.offset > self.size:
			self.offset = self.size

		if offset < 0:
			self.length = offset * -1
		elif length:
			self.length = length
		else:
			self.length = self.size - offset

		if self.length < 0:
			self.length = 0
		elif self.length > self.size:
			self.length = self.size

		if block > 0:
			self.READ_BLOCK_SIZE = block

		io.FileIO.__init__(self, fname, mode)

		# Work around for python 2.6 where FileIO._name is not defined
		try:
			self.name
		except AttributeError:
			self._name = fname

		self.seek(self.offset)

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
			n += io.FileIO.write(self, data[n:])

		return n

	def read(self, n=-1):
		''''
		Reads up to n bytes of data (or to EOF if n is not specified).
		
		io.FileIO.read does not guaruntee that all requested data will be read;
		this method overrides io.FileIO.read and does guaruntee that all data will be read.

		Returns a str object containing the read data.
		'''
		l = 0
		data = b''

		while n < 0 or l < n:
			tmp = io.FileIO.read(self, n-l)
			if tmp:
				data += tmp
				l += len(tmp)
			else:
				break

		return bytes2str(data)

	def seek(self, n, whence=os.SEEK_SET):
		if whence == os.SEEK_SET:
			self.total_read = n
		elif whence == os.SEEK_CUR:
			self.total_read += n
		elif whence == os.SEEK_END:
			self.total_read = self.size + n

		io.FileIO.seek(self, n, whence)

	def read_block(self):
		'''
		Reads in a block of data from the target file.

                Returns a tuple of (str(file block data), block data length).
                '''
		dlen = 0
		data = None

		if self.total_read < self.length:
			# Read in READ_BLOCK_SIZE plus MAX_TRAILING_SIZE bytes, but return a max dlen value
			# of READ_BLOCK_SIZE. This ensures that there is a MAX_TRAILING_SIZE buffer at the
			# end of the returned data in case a signature is found at or near data[dlen].
			data = self.read(self.READ_BLOCK_SIZE + self.MAX_TRAILING_SIZE)

			if data and data is not None:

				# Get the actual length of the read in data
				dlen = len(data)
				seek_offset = dlen - self.READ_BLOCK_SIZE
				
				# If we've read in more data than the scan length, truncate the dlen value
				if (self.total_read + self.READ_BLOCK_SIZE) > self.length:
					dlen = self.length - self.total_read
				# If dlen is the expected rlen size, it should be set to READ_BLOCK_SIZE
				elif dlen == (self.READ_BLOCK_SIZE + self.MAX_TRAILING_SIZE):
					dlen = self.READ_BLOCK_SIZE

				# Increment self.total_read to reflect the amount of data that has been read
				# for processing (actual read size is larger of course, due to the MAX_TRAILING_SIZE
				# buffer of data at the end of each block).
				self.total_read += dlen

				# Seek to the self.total_read offset so the next read can pick up where this one left off.
				if seek_offset > 0:
					self.seek(self.tell() - seek_offset)

		return (data, dlen)

