import magic
import binwalk.config
import binwalk.module
import binwalk.parser
import binwalk.filter
import binwalk.smartsignature
from binwalk.compat import *

class Signature(binwalk.module.Module):

	TITLE = "Signature Scan"

	CLI = [
			binwalk.module.ModuleOption(short='B',
										long='signature',
										kwargs={'enabled' : True},
										description='Scan target file(s) for file signatures'),
			binwalk.module.ModuleOption(short='m',
										long='magic',
										nargs=1,
										kwargs={'magic_files' : []},
										type=[],
										dtype=str,
										description='Specify a custom magic file to use'),
	]

	KWARGS = [
			binwalk.module.ModuleKwarg(name='enabled', default=False),
			binwalk.module.ModuleKwarg(name='magic_files', default=[]),
	]

	HEADER = ["DECIMAL", "HEX", "DESCRIPTION"]
	HEADER_FORMAT = "%-12s  %-12s    %s\n"
	RESULT = ["offset", "offset", "description"]
	RESULT_FORMAT = "%-12d  0x%-12X  %s\n"

	MAGIC_FLAGS = magic.MAGIC_NO_CHECK_TEXT | magic.MAGIC_NO_CHECK_ENCODING | magic.MAGIC_NO_CHECK_APPTYPE | magic.MAGIC_NO_CHECK_TOKENS

	def init(self):
		# Instantiate the config class so we can access file/directory paths
		self.conf = binwalk.config.Config()

		# Create SmartSignature and MagicParser class instances. These are mostly for internal use.
		self.filter = binwalk.filter.MagicFilter()
		self.smart = binwalk.smartsignature.SmartSignature(self.filter, ignore_smart_signatures=False)
		self.parser = binwalk.parser.MagicParser(self.filter, self.smart)

		# Use the system default magic file if no other was specified
		if not self.magic_files:
			# Append the user's magic file first so that those signatures take precedence
			self.magic_files = [
				self.conf.paths['user'][self.conf.BINWALK_MAGIC_FILE],
				self.conf.paths['system'][self.conf.BINWALK_MAGIC_FILE],
			]

		# Parse the magic file(s) and initialize libmagic
		self.mfile = self.parser.parse(self.magic_files)
		self.magic = magic.open(self.MAGIC_FLAGS)
		self.magic.load(str2bytes(self.mfile))
		
		# Once the temporary magic file is loaded into libmagic, we don't need it anymore; delete the temp file
		self.parser.rm_magic_file()

	def scan_file(self, fp):
		while True:
			current_block_offset = 0

			(data, dlen) = fp.read_block()
			if not data:
				break

			block_start = fp.tell() - dlen

			for candidate_offset in self.parser.find_signature_candidates(data, dlen):
				if candidate_offset < current_block_offset:
					continue

				# In python3 we need a bytes object to pass to magic.buffer
				candidate_data = str2bytes(data[candidate_offset:candidate_offset+fp.MAX_TRAILING_SIZE])
			
				# Pass the data to libmagic, and split out multiple results into a list
				magic_result = self.magic.buffer(candidate_data)

				# TODO: Should filter process other validations? Reported size, for example?
				if not self.filter.invalid(magic_result):
					# The smart filter parser returns a dictionary of keyword values and the signature description.
					smart = self.smart.parse(magic_result)
					self.result(description=smart['description'], offset=block_start+candidate_offset)
						
					if smart['jump'] > 0:
						fp.seek(block_start + candidate_offset + smart['jump'])
						current_block_offset = smart['jump']

	def run(self):
		for fp in self.config.target_files:
			self.header()
			self.scan_file(fp)
			self.footer()

