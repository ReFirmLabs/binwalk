#!/usr/bin/env python

import ctypes
import ctypes.util
from binwalk.plugins import *
from binwalk.common import BlockFile

class Plugin:
	'''
	Finds and extracts raw deflate compression streams.
	'''

	ENABLED = False
	SIZE = 64*1024
	DESCRIPTION = "Deflate compressed data stream"

	def __init__(self, binwalk):
		self.binwalk = binwalk

		# The tinfl library is built and installed with binwalk
		self.tinfl = ctypes.cdll.LoadLibrary(ctypes.util.find_library("tinfl"))

		# Add an extraction rule
		if self.binwalk.extractor.enabled:
			self.binwalk.extractor.add_rule(regex=self.DESCRIPTION.lower(), extension="deflate", cmd=self._extractor)

	def pre_scan(self, fp):
		self._deflate_scan(fp)
		return PLUGIN_TERMINATE

	def _extractor(self, file_name):
		if self.tinfl:
			out_file = os.path.splitext(file_name)[0]
			self.tinfl.inflate_raw_file(file_name, out_file)

	def _deflate_scan(self, fp):
		fp.MAX_TRAILING_SIZE = self.SIZE

		# Set these so that the progress report reflects the current scan status
		self.binwalk.scan_length = fp.length
		self.binwalk.total_scanned = 0

		while self.binwalk.total_scanned < self.binwalk.scan_length:
			current_total = self.binwalk.total_scanned

			(data, dlen) = fp.read_block()
			if not data or dlen == 0:
				break

			for i in range(0, dlen):
				if self.tinfl.is_deflated(data[i:], dlen-i, 0):
					loc = fp.offset + current_total + i
					# Update total_scanned here for immediate progress feedback
					self.binwalk.total_scanned = current_total + i
					self.binwalk.display.easy_results(loc, self.DESCRIPTION)

					# Extract the file
					if self.binwalk.extractor.enabled:
						self.binwalk.extractor.extract(loc, self.DESCRIPTION, fp.name, (fp.size - loc))

				if (current_total + i) > self.binwalk.scan_length:
					break

			# Set total_scanned here in case no data streams were identified
			self.binwalk.total_scanned = current_total + dlen

