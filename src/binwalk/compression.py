#!/usr/bin/env python
# Routines to perform Monte Carlo Pi approximation and Chi Squared tests. 
# Used for fingerprinting unknown areas of high entropy (e.g., is this block of high entropy data compressed or encrypted?).
# Inspired by people who actually know what they're doing: http://www.fourmilab.ch/random/

import math
import binwalk.common as common
from binwalk.compat import *

class MonteCarloPi(object):
	'''
	Performs a Monte Carlo Pi approximation.
	Currently unused.
	'''

	def __init__(self):
		'''
		Class constructor.
		
		Returns None.
		'''
		self.reset()

	def reset(self):
		'''
		Reset state to the beginning.
		'''
		self.pi = 0
		self.error = 0
		self.m = 0
		self.n = 0

	def update(self, data):
		'''
		Update the pi approximation with new data.

		@data - A string of bytes to update (length must be >= 6).

		Returns None.
		'''
		c = 0
		dlen = len(data)

		while (c+6) < dlen:
			# Treat 3 bytes as an x coordinate, the next 3 bytes as a y coordinate.
			# Our box is 1x1, so divide by 2^24 to put the x y values inside the box.
			x = ((ord(data[c]) << 16) + (ord(data[c+1]) << 8) + ord(data[c+2])) / 16777216.0
			c += 3
			y = ((ord(data[c]) << 16) + (ord(data[c+1]) << 8) + ord(data[c+2])) / 16777216.0
			c += 3
	
			# Does the x,y point lie inside the circle inscribed within our box, with diameter == 1?
			if ((x**2) + (y**2)) <= 1:
				self.m += 1
			self.n += 1
	
	def montecarlo(self):
		'''
		Approximates the value of Pi based on the provided data.
		
		Returns a tuple of (approximated value of pi, percent deviation).
		'''
		if self.n:
			self.pi = (float(self.m) / float(self.n) * 4.0)

		if self.pi:
			self.error = math.fabs(1.0 - (math.pi / self.pi)) * 100.0
			return (self.pi, self.error)
		else:
			return (0.0, 0.0)

class ChiSquare(object):
	'''
	Performs a Chi Squared test against the provided data.
	'''

	IDEAL = 256.0

	def __init__(self):
		'''
		Class constructor.

		Returns None.
		'''
		self.bytes = {}
		self.freedom = self.IDEAL - 1 
		
		# Initialize the self.bytes dictionary with keys for all possible byte values (0 - 255)
		for i in range(0, int(self.IDEAL)):
			self.bytes[chr(i)] = 0
		
		self.reset()

	def reset(self):
		self.xc2 = 0.0
		self.byte_count = 0

		for key in self.bytes.keys():
			self.bytes[key] = 0		

	def update(self, data):
		'''
		Updates the current byte counts with new data.

		@data - String of bytes to update.

		Returns None.
		'''
		# Count the number of occurances of each byte value
		for i in data:
			self.bytes[i] += 1

		self.byte_count += len(data)

	def chisq(self):
		'''
		Calculate the Chi Square critical value.

		Returns the critical value.
		'''
		expected = self.byte_count / self.IDEAL

		if expected:
			for byte in self.bytes.values():
				self.xc2 += ((byte - expected) ** 2 ) / expected

		return self.xc2

class CompressionEntropyAnalyzer(object):
	'''
	Class wrapper around ChiSquare.
	Performs analysis and attempts to interpret the results.
	'''

	BLOCK_SIZE = 32
	CHI_CUTOFF = 512

	DESCRIPTION = "Statistical Compression Analysis"

	def __init__(self, fname, start, length, binwalk=None):
		'''
		Class constructor.

		@fname    - The file to scan.
		@start    - The start offset to begin analysis at.
		@length   - The number of bytes to analyze.
		@binwalk  - Binwalk class object.

		Returns None.
		'''
		self.fp = common.BlockFile(fname, 'rb', offset=start, length=length)
		
		# Read block size must be at least as large as our analysis block size
		if self.fp.READ_BLOCK_SIZE < self.BLOCK_SIZE:
			self.fp.READ_BLOCK_SIZE = self.BLOCK_SIZE

		self.start = self.fp.offset
		self.length = length
		self.binwalk = binwalk

	def __del__(self):
		try:
			self.fp.close()
		except:
			pass

	def analyze(self):
		'''
		Perform analysis and interpretation.

		Returns a descriptive string containing the results and attempted interpretation.
		'''
		i = 0
		num_error = 0
		analyzer_results = []

		if self.binwalk:
			self.binwalk.display.header(file_name=self.fp.name, description=self.DESCRIPTION)

		chi = ChiSquare()

		while i < self.length:
			j = 0
			(d, dlen) = self.fp.read_block()

			while j < dlen:
				chi.reset()

				data = d[j:j+self.BLOCK_SIZE]
				if len(data) < self.BLOCK_SIZE:
					break

				chi.update(data)

				if chi.chisq() >= self.CHI_CUTOFF:
					num_error += 1
				
				j += self.BLOCK_SIZE

			i += dlen

		if num_error > 0:
			verdict = 'Moderate entropy data, best guess: compressed'
		else:
			verdict = 'High entropy data, best guess: encrypted'

		result = [{'offset' : self.start, 'description' : '%s, size: %d, %d low entropy blocks' % (verdict, self.length, num_error)}]

		if self.binwalk:
			self.binwalk.display.results(self.start, result)
			self.binwalk.display.footer()

		return result

