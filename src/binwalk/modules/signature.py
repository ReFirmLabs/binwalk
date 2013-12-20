import magic
import binwalk.core.parser
import binwalk.core.filter
import binwalk.core.smartsignature
from binwalk.core.compat import *
from binwalk.core.module import Module, Option, Kwarg

class Signature(Module):

	TITLE = "Signature Scan"

	CLI = [
			Option(short='B',
				   long='signature',
				   kwargs={'enabled' : True},
				   description='Scan target file(s) for file signatures'),
			Option(short='m',
				   long='magic',
				   kwargs={'magic_files' : []},
				   type=list,
				   dtype='file',
				   description='Specify a custom magic file to use'),
			Option(short='R',
				   long='raw-bytes',
				   kwargs={'raw_bytes' : None},
				   type=str,
				   description='Specify a sequence of bytes to search for'),
			Option(short='b',
				   long='dumb',
				   kwargs={'dumb_scan' : True},
				   description='Disable smart signature keywords'),
			Option(short='I',
				   long='show-invalid',
				   kwargs={'show_invalid' : True},
				   description='Show results marked as invalid'),
			Option(short='x',
				   long='exclude',
				   kwargs={'exclude_filters' : []},
				   type=list,
				   dtype=str.__name__,
				   description='Exclude results that match <str>'),
			Option(short='y',
				   long='include',
				   kwargs={'include_filters' : []},
				   type=list,
				   dtype=str.__name__,
				   description='Only show results that match <str>'),

	]

	KWARGS = [
			Kwarg(name='enabled', default=False),
			Kwarg(name='dumb_scan', default=False),
			Kwarg(name='show_invalid', default=False),
			Kwarg(name='raw_bytes', default=None),
			Kwarg(name='magic_files', default=[]),
			Kwarg(name='exclude_filters', default=[]),
			Kwarg(name='include_filters', default=[]),
	]

	HEADER = ["DECIMAL", "HEX", "DESCRIPTION"]
	HEADER_FORMAT = "%-12s  %-12s    %s\n"
	RESULT = ["offset", "offset", "description"]
	RESULT_FORMAT = "%-12d  0x%-12X  %s\n"

	MAGIC_FLAGS = magic.MAGIC_NO_CHECK_TEXT | magic.MAGIC_NO_CHECK_ENCODING | magic.MAGIC_NO_CHECK_APPTYPE | magic.MAGIC_NO_CHECK_TOKENS

	def init(self):
		# Create SmartSignature and MagicParser class instances. These are mostly for internal use.
		self.filter = binwalk.core.filter.MagicFilter()
		self.smart = binwalk.core.smartsignature.SmartSignature(self.filter, ignore_smart_signatures=self.dumb_scan)
		self.parser = binwalk.core.parser.MagicParser(self.filter, self.smart)

		# Set any specified include/exclude filters
		for regex in self.exclude_filters:
			self.filter.exclude(regex)
		for regex in self.include_filters:
			self.filter.include(regex)

		# If a raw byte sequence was specified, build a magic file from that instead of using the default magic files
		if self.raw_bytes is not None:
			self.magic_files = [self.parser.file_from_string(self.raw_bytes)]

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
		
		# Once the temporary magic files are loaded into libmagic, we don't need them anymore; delete the temp files
		self.parser.rm_magic_files()

	def validate(self, r):
		'''
		Called automatically by self.result.
		'''
		if not self.show_invalid:
			if not r.description:
				r.valid = False

			if r.size and (r.size + r.offset) > r.file.size:
				r.valid = False

			if r.jump and (r.jump + r.offset) > r.file.size:
				r.valid = False

	def scan_file(self, fp):
		current_file_offset = 0

		while True:
			(data, dlen) = fp.read_block()
			if not data:
				break

			current_block_offset = 0
			block_start = fp.offset + fp.total_read - dlen
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

