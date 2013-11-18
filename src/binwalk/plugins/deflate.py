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
	SIZE = 33*1024
	# To prevent many false positives, only show data that decompressed to a reasonable window size
	MIN_DECOMP_SIZE = 16*1024
	DESCRIPTION = "Deflate compressed data stream"

	def __init__(self, binwalk):
		self.binwalk = binwalk

		# The tinfl library is built and installed with binwalk
		self.tinfl = ctypes.cdll.LoadLibrary(ctypes.util.find_library("tinfl"))

		# Add an extraction rule
		if self.binwalk.extractor.enabled:
			self.binwalk.extractor.add_rule(regex='^%s' % self.DESCRIPTION.lower(), extension="deflate", cmd=self._extractor)

	def pre_scan(self, fp):
		# Make sure we'll be getting enough data for a good decompression test
		if fp.MAX_TRAILING_SIZE < self.SIZE:
			fp.MAX_TRAILING_SIZE = self.SIZE

		self._deflate_scan(fp)

		return PLUGIN_TERMINATE

	def _extractor(self, file_name):
		if self.tinfl:
			out_file = os.path.splitext(file_name)[0]
			self.tinfl.inflate_raw_file(file_name, out_file)

	def _deflate_scan(self, fp):
		# Set these so that the progress report reflects the current scan status
		self.binwalk.scan_length = fp.length
		self.binwalk.total_scanned = 0

		while self.binwalk.total_scanned < self.binwalk.scan_length:
			current_total = self.binwalk.total_scanned

			(data, dlen) = fp.read_block()
			if not data or dlen == 0:
				break

			# dlen == block size, but data includes MAX_TRAILING_SIZE data as well
			actual_dlen = len(data)

			for i in range(0, dlen):
				decomp_size = self.tinfl.is_deflated(data[i:], actual_dlen-i, 0)
				if decomp_size >= self.MIN_DECOMP_SIZE:
					loc = fp.offset + current_total + i
					description = self.DESCRIPTION + ', uncompressed size >= %d' % decomp_size

					# Extract the file
					if self.binwalk.extractor.enabled:
						self.binwalk.extractor.extract(loc, description, fp.name, (fp.size - loc))
					
					# Display results after extraction to be consistent with normal binwalk scans
					self.binwalk.display.easy_results(loc, description)
				
				# Update total_scanned here for immediate progress feedback
				self.binwalk.total_scanned = current_total + i

				if (current_total + i) > self.binwalk.scan_length:
					break

			# Set total_scanned here in case no data streams were identified
			self.binwalk.total_scanned = current_total + dlen

