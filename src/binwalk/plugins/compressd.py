import ctypes
import ctypes.util
from binwalk.common import *

class Plugin:
	'''
	Searches for and validates compress'd data.
	'''

	READ_SIZE = 64

	def __init__(self, module):
		self.fd = None
		self.comp = None

		if module.name == 'Signature':
			self.comp = ctypes.cdll.LoadLibrary(ctypes.util.find_library("compress42"))

	def scan(self, result):
		if self.comp:
			if result.file and result.description.lower().startswith("compress'd data"):
				fd = BlockFile(result.file.name, "r")
				fd.seek(result.offset)

				compressed_data = fd.read(self.READ_SIZE)
                        
				if not self.comp.is_compressed(compressed_data, len(compressed_data)):
					result.valid = False

				fd.close()

