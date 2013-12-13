import magic
import binwalk.config
import binwalk.module
import binwalk.parser
import binwalk.filter
import binwalk.smartsignature
from binwalk.compat import *

class Signature(binwalk.module.Module):

	CLI = [
			binwalk.module.ModuleOption(short='B',
										long='signature',
										kwargs={'enabled' : True}),
	]

	KWARGS = [
			binwalk.module.ModuleKwarg(name='enabled', default=False),
			binwalk.module.ModuleKwarg(name='magic_files', default=[]),
	]

	HEADER="BINWALK"
	HEADER_FORMAT="%s\n"
	RESULT=["offset", "offset", "description"]
	RESULT_FORMAT="%d  0x%X  %s\n"

	MAGIC_FLAGS = magic.MAGIC_NO_CHECK_TEXT | magic.MAGIC_NO_CHECK_ENCODING | magic.MAGIC_NO_CHECK_APPTYPE | magic.MAGIC_NO_CHECK_TOKENS

	def init(self):
		# Instantiate the config class so we can access file/directory paths
		self.conf = binwalk.config.Config()

		# Create SmartSignature and MagicParser class instances. These are mostly for internal use.
		self.filter = binwalk.filter.MagicFilter()
		self.smart = binwalk.smartsignature.SmartSignature(self.filter, ignore_smart_signatures=False)
		self.parser = binwalk.parser.MagicParser(self.filter, self.smart)

		# Use the system default magic file if no other was specified
		if not self.magic_files or self.magic_files is None:
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
		data = fp.read()

		for candidate in self.parser.find_signature_candidates(data, len(data)):
			# In python3 we need a bytes object to pass to magic.buffer
			candidate_data = str2bytes(data[candidate:candidate+fp.MAX_TRAILING_SIZE])
			
			# Pass the data to libmagic, and split out multiple results into a list
			for magic_result in self.parser.split(self.magic.buffer(candidate_data)):
				if not self.filter.invalid(magic_result):
					# The smart filter parser returns a dictionary of keyword values and the signature description.
					smart = self.smart.parse(magic_result)
					self.result(description=smart['description'], offset=candidate)

	def run(self):
		for fp in self.config.target_files:
			self.scan_file(fp)

