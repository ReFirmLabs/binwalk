import binwalk.core.C
from binwalk.core.common import *

class Plugin(object):
	'''
	Searches for and validates compress'd data.
	'''

	READ_SIZE = 64

	COMPRESS42 = "compress42"
	COMPRESS42_FUNCTIONS = [
		binwalk.core.C.Function(name="is_compressed", type=bool),
	]

	def __init__(self, module):
		self.fd = None
		self.comp = None

		if module.name == 'Signature':
			self.comp = binwalk.core.C.Library(self.COMPRESS42, self.COMPRESS42_FUNCTIONS)

	def scan(self, result):
		if self.comp:
			if result.file and result.description.lower().startswith("compress'd data"):
				fd = BlockFile(result.file.name, "r", offset=result.offset, length=self.READ_SIZE)
				compressed_data = fd.read(self.READ_SIZE)
				fd.close()
                        
				if not self.comp.is_compressed(compressed_data, len(compressed_data)):
					result.valid = False


