import os
import math
import binwalk.core.common
from binwalk.core.compat import *
from binwalk.core.module import Module, Option, Kwarg

class Entropy(Module):

	XLABEL = 'Offset'
	YLABEL = 'Entropy'

	XUNITS = 'B'
	YUNITS = 'E'

	FILE_WIDTH = 1024
	FILE_FORMAT = 'png'

	COLORS = ['r', 'g', 'c', 'b', 'm']

	TITLE = "Entropy"

	CLI = [
			Option(short='E',
				   long='entropy',
				   kwargs={'enabled' : True},
				   description='Calculate file entropy'),
			Option(short='J',
				   long='save-plot',
				   kwargs={'save_plot' : True},
				   description='Save plot as a PNG (implied if multiple files are specified)'),
			Option(short='N',
				   long='no-plot',
				   kwargs={'do_plot' : False},
				   description='Do not generate an entropy plot graph'),
			Option(short='Q',
				   long='no-legend',
				   kwargs={'show_legend' : False},
				   description='Omit the legend from the entropy plot graph (implied if multiple files are specified)'),
	]

	KWARGS = [
			Kwarg(name='enabled', default=False),
			Kwarg(name='save_plot', default=False),
			Kwarg(name='do_plot', default=True),
			Kwarg(name='show_legend', default=True),
			Kwarg(name='block_size', default=1024),
	]

	# Run this module last so that it can process all other module's results and overlay them on the entropy graph
	PRIORITY = 0

	def init(self):
		self.HEADER[-1] = "ENTROPY"
		self.algorithm = self.shannon
		self.display_results = True
		self.max_description_length = 0
		self.markers = []

		# Automatically save plots if there is more than one file specified
		if len(self.config.target_files) > 1:
			self.save_plot = True
			self.show_legend = False

		# Get a list of all other module's results to mark on the entropy graph
		for (module, obj) in iterator(self.modules):
			for result in obj.results:
				if result.description:
					description = result.description.split(',')[0]
					if len(description) > self.max_description_length:
						self.max_description_length = len(description)
					self.markers.append((result.offset, description))

		# If other modules have been run and they produced results, don't spam the terminal with entropy results
		if self.markers:
			self.display_results = False

		if self.config.block:
			self.block_size = self.config.block

	def run(self):
		for fp in self.config.target_files:

			if self.display_results:
				self.header()

			self.calculate_file_entropy(fp)

			if self.display_results:
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
				r = self.result(offset=(file_offset + i), file=fp, entropy=entropy, description=("%f" % entropy), display=self.display_results)
				i += self.block_size

		if self.do_plot:
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

	def plot_entropy(self, fname):
		import numpy as np
		import pyqtgraph as pg
		from pyqtgraph.Qt import QtCore, QtGui

		i = 0
		x = []
		y = []
		plotted_colors = {}

		for r in self.results:
			x.append(r.offset)
			y.append(r.entropy)

		plt = pg.plot(title=fname, clear=True)

		plt.plot(x, y, pen='y')

		if self.show_legend and self.markers:
			plt.addLegend(size=(self.max_description_length*10, 0))

			for (offset, description) in self.markers:
				# If this description has already been plotted at a different offset, we need to 
				# use the same color for the marker, but set the description to None to prevent
				# duplicate entries in the graph legend.
				#
				# Else, get the next color and use it to mark descriptions of this type.
				if has_key(plotted_colors, description):
					color = plotted_colors[description]
					description = None
				else:
					color = self.COLORS[i]
					plotted_colors[description] = color

					i += 1
					if i >= len(self.COLORS):
						i = 0

				plt.plot(x=[offset,offset], y=[0,1.1], name=description, pen=pg.mkPen(color, width=2.5))

		if self.save_plot:
			exporter = pg.exporters.ImageExporter.ImageExporter(plt.plotItem)
			exporter.parameters()['width'] = self.FILE_WIDTH
			exporter.export(binwalk.core.common.unique_file_name(os.path.basename(fname), self.FILE_FORMAT))
		else:
			plt.setLabel('left', self.YLABEL, units=self.YUNITS)
			plt.setLabel('bottom', self.XLABEL, units=self.XUNITS)
			QtGui.QApplication.instance().exec_()

