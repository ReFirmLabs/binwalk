import ctypes
import ctypes.util
from binwalk.common import BlockFile

class Plugin:
	'''
	Searches for and validates zlib compressed data.
	'''

	MIN_DECOMP_SIZE = 16 * 1024
	MAX_DATA_SIZE = 33 * 1024

	def __init__(self, module):
		self.tinfl = None
		self.module = module

		# Only initialize this plugin if this is a signature scan
		if module.name == 'Signature':
			# Load libtinfl.so
			self.tinfl = ctypes.cdll.LoadLibrary(ctypes.util.find_library('tinfl'))

	def scan(self, result):
		# If this result is a zlib signature match, try to decompress the data
		if self.tinfl and result.file and result.description.lower().startswith('zlib'):
			# Seek to and read the suspected zlib data
			fd = BlockFile(result.file.name, offset=result.offset, swap=self.module.config.swap_size)
			data = fd.read(self.MAX_DATA_SIZE)
			fd.close()

			# Check if this is valid zlib data
			decomp_size = self.tinfl.is_deflated(data, len(data), 1)
			if decomp_size > 0:
				result.description += ", uncompressed size >= %d" % decomp_size
			else:
				result.valid = False

