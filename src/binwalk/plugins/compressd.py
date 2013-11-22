import ctypes
import ctypes.util
from binwalk.common import *
from binwalk.plugins import *

class Plugin:
	'''
	Searches for and validates compress'd data.
	'''

	ENABLED = True
	READ_SIZE = 64

	def __init__(self, binwalk):
		self.fd = None
		self.comp = None
		self.binwalk = binwalk
		
		if binwalk.scan_type == binwalk.BINWALK:
			self.comp = ctypes.cdll.LoadLibrary(ctypes.util.find_library("compress42"))
			if self.comp:
				binwalk.magic_files.append(binwalk.config.find_magic_file('compressd'))

	def __del__(self):
		try:
			self.fd.close()
		except:
			pass

	def pre_scan(self, fd):
		try:
			if self.comp:
				self.fd = BlockFile(fd.name, 'r')
		except:
			pass

	def callback(self, results):
		if self.fd and results['description'].lower().startswith("compress'd data"):
			self.fd.seek(results['offset'])
			compressed_data = self.fd.read(self.READ_SIZE)
                        
			if not self.comp.is_compressed(compressed_data, len(compressed_data)):
				return (PLUGIN_NO_DISPLAY | PLUGIN_NO_EXTRACT)

