#!/usr/bin/env python

import ctypes
import ctypes.util
from binwalk.plugins import *
from binwalk.common import BlockFile

class Plugin:
	'''
	Searches for raw deflate compression streams.
	'''

	ENABLED = False
	SIZE = 64*1024
	DESCRIPTION = "Deflate compressed data stream"

	def __init__(self, binwalk):
		self.binwalk = binwalk

		# The tinfl library is built and installed with binwalk
		self.tinfl = ctypes.cdll.LoadLibrary(ctypes.util.find_library("tinfl"))

		if self.binwalk.extractor.enabled:
			# TODO: Add python extractor rule
			pass

	def pre_scan(self, fp):
		self._deflate_scan(fp)
		return PLUGIN_TERMINATE

	def _extractor(self, file_name):
		processed = 0
		inflated_data = ''
		fd = BlockFile(file_name, 'rb')
		fd.READ_BLOCK_SIZE = self.SIZE

		while processed < fd.length:
			(data, dlen) = fd.read_block()

			inflated_block = self.tinfl.inflate_block(data, dlen)
			if inflated_block:
				inflated_data += inflated_block
			else:
				break

			processed += dlen

		fd.close()
		
		print "%s inflated to %d bytes" % (file_name, len(inflated_data))

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

				if (current_total + i) > self.binwalk.scan_length:
					break

			# Set total_scanned here in case no data streams were identified
			self.binwalk.total_scanned = current_total + dlen

