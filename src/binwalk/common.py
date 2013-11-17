# Common functions.
import io
import os
import re
from binwalk.compat import *

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

class BlockFile(io.FileIO):
	'''
	Abstraction class to handle reading data from files in blocks.
	Necessary for large files.
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

	def __init__(self, fname, mode='r', length=0, offset=0):
		'''
		Class constructor.

		@fname  - Path to the file to be opened.
		@mode   - Mode to open the file in (default: 'r').
		@length - Maximum number of bytes to read from the file via self.block_read().
		@offset - Offset at which to start reading from the file.

		Returns None.
		'''
		self.total_read = 0
		
		try:
			self.size = file_size(fname)
		except:
			self.size = 0

		if offset < 0:
			self.offset = self.size + offset
		else:
			self.offset = offset

		if length:
			self.length = length
		else:
			self.length = self.size

		io.FileIO.__init__(self, fname, mode)

		self.seek(self.offset)
			

	def read_block(self):
		'''
		Reads in a block of data from the target file.

                Returns a tuple of (file block data, block data length).
                '''
		dlen = 0
		data = None

		if self.total_read < self.length:
			# Read in READ_BLOCK_SIZE plus MAX_TRAILING_SIZE bytes, but return a max dlen value
			# of READ_BLOCK_SIZE. This ensures that there is a MAX_TRAILING_SIZE buffer at the
			# end of the returned data in case a signature is found at or near data[dlen].
			data = self.read(self.READ_BLOCK_SIZE + self.MAX_TRAILING_SIZE)

			if data and data is not None:
				data = bytes2str(data)

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

