from binwalk.plugins import *

class Plugin:
	'''
	Validates ARM instructions during opcode scans.
	'''

	BITMASK = 0x83FF
	BITMASK_SIZE = 2

	def __init__(self, binwalk):
		self.fd = None

		if binwalk.scan_type == binwalk.BINARCH:
			self.enabled = True
		else:
			self.enabled = False

	def pre_scan(self, fd):
		if self.enabled:
			self.fd = open(fd.name, 'rb')

	def callback(self, results):
		if self.fd:
			data = ''
			
			try:
				if results['description'].startswith('ARM instruction'):
					self.fd.seek(results['offset'])
					data = self.fd.read(self.BITMASK_SIZE)
					data = data[1] + data[0]
				elif results['description'].startswith('ARMEB instruction'):
					self.fd.seek(results['offset']+self.BITMASK_SIZE)
					data = self.fd.read(self.BITMASK_SIZE)

				if data:
					registers = int(data.encode('hex'), 16)
					if (registers & self.BITMASK) != registers:
						return PLUGIN_NO_DISPLAY
			except:
				pass
			

	def post_scan(self, fd):
		try:
			self.fd.close()
		except:
			pass
			
