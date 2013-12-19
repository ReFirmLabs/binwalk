import magic
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
		# Create SmartSignature and MagicParser class instances. These are mostly for internal use.
		self.filter = binwalk.filter.MagicFilter()
		self.smart = binwalk.smartsignature.SmartSignature(self.filter, ignore_smart_signatures=False)
		self.parser = binwalk.parser.MagicParser(self.filter, self.smart)

		# Use the system default magic file if no other was specified
		if not self.magic_files:
			# Append the user's magic file first so that those signatures take precedence
			self.magic_files = [
				self.config.settings.paths['user'][self.config.settings.BINWALK_MAGIC_FILE],
				self.config.settings.paths['system'][self.config.settings.BINWALK_MAGIC_FILE],
			]

		# Parse the magic file(s) and initialize libmagic
		self.mfile = self.parser.parse(self.magic_files)
		self.magic = magic.open(self.MAGIC_FLAGS)
		self.magic.load(str2bytes(self.mfile))
		
		# Once the temporary magic file is loaded into libmagic, we don't need it anymore; delete the temp file
		self.parser.rm_magic_file()

	def validate(self, r):
		'''
		Called automatically by self.result.
		'''
		if not r.description:
			r.valid = False

		if r.size and (r.size + r.offset) > r.file.size:
			r.valid = False

		if r.jump and (r.jump + r.offset) > r.file.size:
			r.valid = False

	def scan_file(self, fp):
		while True:
			(data, dlen) = fp.read_block()
			if not data:
				break

			current_block_offset = 0
			block_start = fp.tell() - dlen
			self.status.completed = block_start - fp.offset

			for candidate_offset in self.parser.find_signature_candidates(data, dlen):
				if candidate_offset < current_block_offset:
					continue

				# In python3 we need a bytes object to pass to magic.buffer
				candidate_data = str2bytes(data[candidate_offset:candidate_offset+fp.MAX_TRAILING_SIZE])
			
				# Pass the data to libmagic, and split out multiple results into a list
				magic_result = self.magic.buffer(candidate_data)

				if self.filter.valid_magic_result(magic_result):
					# The smart filter parser returns a dictionary of keyword values and the signature description.
					r = self.smart.parse(magic_result)
					r.offset = block_start + candidate_offset + r.adjust
					r.file = fp

					self.result(r=r)
					
					if r.valid and r.jump > 0:
						fp.seek(r.offset + r.jump)
						current_block_offset = r.jump

	def run(self):
		for fp in self.config.target_files:
			self.header()
			
			self.status.clear()
			self.status.total = fp.size
			self.status.completed = 0

			self.scan_file(fp)
			
			self.footer()

