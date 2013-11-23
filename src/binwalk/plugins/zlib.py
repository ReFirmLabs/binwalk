import ctypes
import ctypes.util
from binwalk.plugins import *
from binwalk.common import BlockFile

class Plugin:
	'''
	Searches for and validates zlib compressed data.
	'''

	MIN_DECOMP_SIZE = 16*1024
	MAX_DATA_SIZE = 33 * 1024

	def __init__(self, binwalk):
		self.fd = None
		self.tinfl = None
		zlib_magic_file = binwalk.config.find_magic_file('zlib')

		# Only initialize this plugin if this is a normal binwalk signature scan
		if binwalk.scan_type == binwalk.BINWALK:
			# Load libtinfl.so
			self.tinfl = ctypes.cdll.LoadLibrary(ctypes.util.find_library('tinfl'))
			if self.tinfl:
				# Add the zlib file to the list of magic files
				binwalk.magic_files.append(zlib_magic_file)
		# Else, be sure to unload the zlib file from the list of magic signatures
		elif zlib_magic_file in binwalk.magic_files:
			binwalk.magic_files.pop(binwalk.magic_files.index(zlib_magic_file))

	def pre_scan(self, fd):
		if self.tinfl:
			self.fd = BlockFile(fd.name, 'r')

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

