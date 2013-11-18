import ctypes
import ctypes.util
from binwalk.plugins import *

class Plugin:
	'''
	Searches for and validates zlib compressed data.
	'''

	MIN_DECOMP_SIZE = 1
	MAX_DATA_SIZE = 33 * 1024

	def __init__(self, binwalk):
		self.fd = None
		self.tinfl = None

		if binwalk.scan_type == binwalk.BINWALK:
			# Add the zlib file to the list of magic files
			binwalk.magic_files.append(binwalk.config.find_magic_file('zlib'))
			# Load libtinfl.so
			self.tinfl = ctypes.cdll.LoadLibrary(ctypes.util.find_library('tinfl'))
	
	def pre_scan(self, fd):
		if self.tinfl:
			self.fd = open(fd.name, 'rb')

	def callback(self, result):

		# If this result is a zlib signature match, try to decompress the data
		if self.fd and result['description'].lower().startswith('zlib'):
			# Seek to and read the suspected zlib data
			self.fd.seek(result['offset'])
			data = self.fd.read(self.MAX_DATA_SIZE)
			
			# Check if this is valid zlib data
			decomp_size = self.tinfl.is_deflated(data, len(data), 1)
			if decomp_size > 0:
				result['description'] += ", uncompressed size >= %d" % decomp_size
			else:
				return (PLUGIN_NO_DISPLAY | PLUGIN_NO_EXTRACT)
		
		return PLUGIN_CONTINUE

	def post_scan(self, fd):
		if self.fd:
			self.fd.close()

