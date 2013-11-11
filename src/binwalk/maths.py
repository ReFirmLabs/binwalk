#!/usr/bin/env python
# Routines to perform Monte Carlo Pi approximation and Chi Squared tests. 
# Used for fingerprinting unknown areas of high entropy (e.g., is this block of high entropy data compressed or encrypted?).
# Inspired by people who actually know what they're doing: http://www.fourmilab.ch/random/

import math

class MonteCarloPi(object):
	'''
	Performs a Monte Carlo Pi approximation.
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

class MathAnalyzer(object):
	'''
	Class wrapper aroung ChiSquare and MonteCarloPi.
	Performs analysis and attempts to interpret the results.
	'''

	# Data blocks must be in multiples of 6 for the monte carlo pi approximation
	BLOCK_SIZE = 32
	CHI_CUTOFF = 512

	def __init__(self, fp, start, length):
		'''
		Class constructor.

		@fp     - A seekable, readable, file object that will be the data source.
		@start  - The start offset to begin analysis at.
		@length - The number of bytes to analyze.

		Returns None.
		'''
		self.fp = fp
		self.start = start
		self.length = length

	def analyze(self):
		'''
		Perform analysis and interpretation.

		Returns a descriptive string containing the results and attempted interpretation.
		'''
		i = 0
		num_error = 0
		analyzer_results = []

		chi = ChiSquare()

		self.fp.seek(self.start)
		while i < self.length:
			rsize = self.length - i
			if rsize > self.BLOCK_SIZE:
				rsize = self.BLOCK_SIZE

			chi.reset()
			chi.update(self.fp.read(rsize))

			if chi.chisq() >= self.CHI_CUTOFF:
				num_error += 1

			i += rsize

		if num_error > 0:
			verdict = 'Low/medium entropy data block'
		else:
			verdict = 'High entropy data block'

		result = '%s, %d low entropy blocks' % (verdict, num_error)

		return result

if __name__ == "__main__":
	import sys

	rsize = 0
	largest = (0, 0)
	num_error = 0
	data = open(sys.argv[1], 'rb').read()

	try:
		block_size = int(sys.argv[2], 0)
	except:
		block_size = 32

	chi = ChiSquare()
	
	while rsize < len(data):
		chi.reset()

		d = data[rsize:rsize+block_size]
		if d < block_size:
			break

		chi.update(d)
		if chi.chisq() >= 512:
			sys.stderr.write("0x%X -> %d\n" % (rsize, chi.xc2))
			num_error += 1
		if chi.xc2 >= largest[1]:
			largest = (rsize, chi.xc2)

		rsize += block_size

	sys.stderr.write("Number of deviations: %d\n" % num_error)
	sys.stderr.write("Largest deviation: %d at offset 0x%X\n" % (largest[1], largest[0]))

	print "Data:",
	if num_error != 0:
		print "Compressed"
	else:
		print "Encrypted"

	print "Confidence:",
	if num_error >= 5 or num_error == 0:
		print "High"
	elif num_error in [3,4]:
		print "Medium"
	else:
		print "Low"


