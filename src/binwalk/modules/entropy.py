import math
from binwalk.core.module import Module, Option, Kwarg

class Entropy(Module):

	XLABEL = 'Offset'
	YLABEL = 'Entropy'

	XUNITS = 'B'
	YUNITS = 'E'

	TITLE = "Entropy"

	CLI = [
			Option(short='E',
				   long='entropy',
				   kwargs={'enabled' : True},
				   description='Calculate file entropy'),
	]

	KWARGS = [
			Kwarg(name='enabled', default=False),
			Kwarg(name='block_size', default=1024),
	]

	def init(self):
		self.entropy_results = {}
		self.algorithm = self.shannon
		if self.config.block:
			self.block_size = self.config.block

	def run(self):
		for fp in self.config.target_files:
			self.header()
			self.calculate_file_entropy(fp)
			self.footer()

	def calculate_file_entropy(self, fp):
		# Clear results from any previously analyzed files
		self.clear(results=True)

		while True:
			file_offset = fp.tell()

			(data, dlen) = fp.read_block()
			if not data:
				break

			i = 0
			while i < dlen:
				entropy = self.algorithm(data[i:i+self.block_size])
				r = self.result(offset=(file_offset + i), file=fp, entropy=entropy, description=("%f" % entropy))
				i += self.block_size

		self.plot_entropy(fp.name)

	def shannon(self, data):
		'''
		Performs a Shannon entropy analysis on a given block of data.
		'''
		entropy = 0

		if data:
			for x in range(0, 256):
				p_x = float(data.count(chr(x))) / len(data)
				if p_x > 0:
					entropy += - p_x*math.log(p_x, 2)

		return (entropy / 8)

	def gzip(self, data, truncate=True):
		'''
		Performs an entropy analysis based on zlib compression ratio.
		This is faster than the shannon entropy analysis, but not as accurate.
		'''
		# Entropy is a simple ratio of: <zlib compressed size> / <original size>
		e = float(float(len(zlib.compress(data, 9))) / float(len(data)))

		if truncate and e > 1.0:
			e = 1.0

		return e

	def plot_entropy(self, title):
		import numpy as np
		import pyqtgraph as pg
		from pyqtgraph.Qt import QtCore, QtGui

		x = []
		y = []

		for r in self.results:
			x.append(r.offset)
			y.append(r.entropy)

		plt = pg.plot(title=title, clear=True)

		plt.plot(x, y, pen='y') #pen='b'

		plt.setLabel('left', self.YLABEL, units=self.YUNITS)
		plt.setLabel('bottom', self.XLABEL, units=self.XUNITS)
		QtGui.QApplication.instance().exec_()

