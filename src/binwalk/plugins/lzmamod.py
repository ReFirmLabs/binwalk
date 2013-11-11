import os
import shutil
from binwalk.common import BlockFile

class Plugin:
	'''
	Finds and extracts modified LZMA files commonly found in cable modems.
	Based on Bernardo Rodrigues' work: http://w00tsec.blogspot.com/2013/11/unpacking-firmware-images-from-cable.html
	'''

	ENABLED = True

	FAKE_LZMA_SIZE = "\x00\x00\x00\x10\x00\x00\x00\x00"
	SIGNATURE = "lzma compressed data"

	def __init__(self, binwalk):
		self.binwalk = binwalk
		self.original_cmd = ''

		if self.binwalk.extractor.enabled:
			# Replace the existing LZMA extraction command with our own
			rules = self.binwalk.extractor.get_rules()
			for i in range(0, len(rules)):
				if rules[i]['regex'].match(self.SIGNATURE):
					self.original_cmd = rules[i]['cmd']
					rules[i]['cmd'] = self.lzma_cable_extractor
					break

	def lzma_cable_extractor(self, fname):
		# Try extracting the LZMA file without modification first
		if not self.binwalk.extractor.execute(self.original_cmd, fname):
			out_name = os.path.splitext(fname)[0] + '-patched' + os.path.splitext(fname)[1]
			fp_out = open(out_name, 'wb')
			fp_in = BlockFile(fname)
			fp_in.MAX_TRAILING_SIZE = 0
			i = 0

			while i < fp_in.length:
				(data, dlen) = fp_in.read_block()
				
				if i == 0:
					fp_out.write(data[0:5] + self.FAKE_LZMA_SIZE + data[5:])
				else:
					fp_out.write(data)
	
				i += dlen

			fp_in.close()
			fp_out.close()

			# Overwrite the original file so that it can be cleaned up if -r was specified
			shutil.move(out_name, fname)
			self.binwalk.extractor.execute(self.original_cmd, fname)

	def pre_parser(self, result):
		# The modified cable modem LZMA headers all have valid dictionary sizes and a properties byte of 0x5D.
		if result['description'].lower().startswith(self.SIGNATURE) and "invalid uncompressed size" in result['description']:
			if "properties: 0x5D" in result['description'] and "invalid dictionary size" not in result['description']:
				result['invalid'] = False
				result['description'] = result['description'].split("invalid uncompressed size")[0] + "missing uncompressed size"

