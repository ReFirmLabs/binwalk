import zlib
import math
import os.path
import binwalk.plugins as plugins
import binwalk.common as common
import binwalk.compression as compression
from binwalk.compat import *

class PlotEntropy(object):
	'''
	Class to plot entropy data on a graph.
	'''

	XLABEL = 'Offset'
	YLABEL = 'Entropy'

	XUNITS = 'B'
	YUNITS = 'E'

	COLORS = ['r', 'g', 'c', 'b', 'm']

	FILE_WIDTH = 1024
	FILE_FORMAT = 'png'

	def __init__(self, x, y, title='Entropy', average=0, file_results={}, show_legend=True, save=False):
		'''
		Plots entropy data.

		@x            - List of graph x-coordinates (i.e., data offsets).
		@y            - List of graph y-coordinates (i.e., entropy for each offset).
		@title        - Graph title.
		@average      - The average entropy.
		@file_results - Binwalk results, if any.
		@show_legend  - Set to False to not generate a color-coded legend and plotted x coordinates for the graph.
		@save         - If set to True, graph will be saved to disk rather than displayed.

		Returns None.
		'''
		import numpy as np
		import pyqtgraph as pg
		from pyqtgraph.Qt import QtCore, QtGui

		i = 0
		descriptions = {}
		plotted_colors = {}
		max_description_length = None

		for (offset, results) in file_results:
			description = results[0]['description'].split(',')[0]
			desc_len = len(description)

			if not max_description_length or desc_len > max_description_length:
				max_description_length = desc_len

			if has_key(descriptions, offset):
				descriptions[offset].append(description)
			else:
				descriptions[offset] = [description]
			

		#pg.setConfigOption('background', 'w')
		#pg.setConfigOption('foreground', 'k')
		
		plt = pg.plot(title=title, clear=True)

		plt.plot(x, y, pen='y') #pen='b'
		if file_results and show_legend:
			plt.addLegend(size=(max_description_length*10, 0)) 

		# Don't really like the way pyqtgraph draws these infinite horizontal lines
		#if average:
		#	plt.addLine(y=average, pen='r')

		if descriptions:
			ordered_offsets = get_keys(descriptions)
			ordered_offsets.sort()

			for offset in ordered_offsets:
				for description in descriptions[offset]:

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
				
		if save:
			exporter = pg.exporters.ImageExporter.ImageExporter(plt.plotItem)
			exporter.parameters()['width'] = self.FILE_WIDTH
			exporter.export(common.unique_file_name(title, self.FILE_FORMAT))
		else:
			# Only set the axis labels if we're displaying a live window (axis labels aren't well-placed when saving directly to file)
			plt.setLabel('left', self.YLABEL, units=self.YUNITS)
			plt.setLabel('bottom', self.XLABEL, units=self.XUNITS)
			QtGui.QApplication.instance().exec_()


class FileEntropy(object):
	'''
	Class for analyzing and plotting data entropy for a file.
	Preferred to use the Entropy class instead of calling FileEntropy directly.
	'''

	DEFAULT_BLOCK_SIZE = 1024
	ENTROPY_TRIGGER = 0.9
	ENTROPY_MAX = 0.95

	def __init__(self, file_name=None, binwalk=None, offset=0, length=None, block=DEFAULT_BLOCK_SIZE, plugins=None, file_results=[], compcheck=False):
		'''
		Class constructor.

		@file_name    - The path to the file to analyze.
		@binwalk      - An instance of the Binwalk class.
		@offset       - The offset into the data to begin analysis.
		@length       - The number of bytes to analyze.
		@block        - The size of the data blocks to analyze.
		@plugins      - Instance of the Plugins class.
		@file_results - Scan results to overlay on the entropy plot graph.
		@compcheck    - Set to True to enable entropy compression detection.

		Returns None.
		'''
		self.start = offset
		self.length = length
		self.block = block
		self.binwalk = binwalk
		self.plugins = plugins
		self.total_read = 0
		self.current_data_block = ''
		self.current_data_block_len = 0
		self.current_data_block_offset = 0
		self.file_results = file_results
		self.do_chisq = compcheck

		if file_name is None:
			raise Exception("Entropy.__init__ requires at least the file_name option")

		if not self.length:
			self.length = 0

		if not self.start:
			self.start = 0

		if not self.block:
			self.block = self.DEFAULT_BLOCK_SIZE
			
		self.fd = common.BlockFile(file_name, 'r', offset=self.start, length=self.length)
		self.start = self.fd.offset
		self.fd.MAX_TRAILING_SIZE = 0
		if self.fd.READ_BLOCK_SIZE < self.block:
			self.fd.READ_BLOCK_SIZE = self.block

		if self.binwalk:
			# Set the total_scanned and scan_length values for plugins and status display messages
			self.binwalk.total_scanned = 0
			self.binwalk.scan_length = self.fd.length

	def __enter__(self):
		return self

	def __del__(self):
		self.cleanup()

	def __exit__(self, t, v, traceback):
		self.cleanup()

	def cleanup(self):
		'''
		Clean up any open file objects.
		Called internally by __del__ and __exit__.

		Returns None.
		'''
		try:
			self.fd.close()
		except:
			pass

	def _read_block(self):
		offset = self.total_read

		if self.current_data_block_offset >= self.current_data_block_len:
			self.current_data_block_offset = 0
			(self.current_data_block, self.current_data_block_len) = self.fd.read_block()

		if self.current_data_block and (self.current_data_block_len-self.current_data_block_offset) >= self.block:
			data = self.current_data_block[self.current_data_block_offset:self.current_data_block_offset+self.block]
			dlen = self.block
		else:
			data = ''
			dlen = 0

		self.current_data_block_offset += dlen
		self.total_read += dlen
		
		if self.binwalk:
			self.binwalk.total_scanned = self.total_read

		return (dlen, data, offset+self.start)

	def gzip(self, offset, data, truncate=True):
		'''
		Performs an entropy analysis based on zlib compression ratio.
		This is faster than the shannon entropy analysis, but not as accurate.
		'''
		# Entropy is a simple ratio of: <zlib compressed size> / <original size>
		e = float(float(len(zlib.compress(data, 9))) / float(len(data)))

		if truncate and e > 1.0:
			e = 1.0

		return e

	def shannon(self, offset, data):
		'''
		Performs a Shannon entropy analysis on a given block of data.
		'''
		entropy = 0
		dlen = len(data)

		if not data:
			return 0

		for x in range(256):
			p_x = float(data.count(chr(x))) / dlen
			if p_x > 0:
				entropy += - p_x*math.log(p_x, 2)

		return (entropy / 8)

	def _do_analysis(self, algorithm):
		'''
		Performs an entropy analysis using the provided algorithm.

		@algorithm - A function/method to call which returns an entropy value.

		Returns a tuple of ([x-coordinates], [y-coordinates], average_entropy), where:

			o x-coordinates = A list of offsets analyzed inside the data.
			o y-coordinates = A corresponding list of entropy for each offset.
		'''
		offsets = []
		entropy = []
		average = 0
		total = 0
		self.total_read = 0
		plug_ret = plugins.PLUGIN_CONTINUE
		plug_pre_ret = plugins.PLUGIN_CONTINUE

		if self.plugins:
			plug_pre_ret = self.plugins._pre_scan_callbacks(self.fd)

		while not ((plug_pre_ret | plug_ret) & plugins.PLUGIN_TERMINATE):
			(dlen, data, offset) = self._read_block()
			if not dlen or not data:
				break

			e = algorithm(offset, data)

			results = {'description' : '%f' % e, 'offset' : offset}

			if self.plugins:
				plug_ret = self.plugins._scan_callbacks(results)
				offset = results['offset']
				e = float(results['description'])

			if not ((plug_pre_ret | plug_ret) & (plugins.PLUGIN_TERMINATE | plugins.PLUGIN_NO_DISPLAY)):
				if self.binwalk and not self.do_chisq:
					self.binwalk.display.results(offset, [results])

				entropy.append(e)
				offsets.append(offset)
				total += e

		try:
			# This results in a divide by zero if one/all plugins returns PLUGIN_TERMINATE or PLUGIN_NO_DISPLAY,
			# or if the file being scanned is a zero-size file.
			average = float(float(total) / float(len(offsets)))
		except:
			pass

		if self.plugins:
			self.plugins._post_scan_callbacks(self.fd)
		
		if self.do_chisq:
			self._look_for_compression(offsets, entropy)
	
		return (offsets, entropy, average)

	def _look_for_compression(self, x, y):
		'''
		Analyzes areas of high entropy for signs of compression or encryption and displays the results.
		'''
		trigger = self.ENTROPY_TRIGGER
		pairs = []
		scan_pairs = []
		index = -1
		total = 0

		if not self.file_results:
			for j in range(0, len(x)):
				if y[j] >= trigger and (j == 0 or y[j-1] < trigger):
					pairs.append([x[j]])
					index = len(pairs) - 1
				elif y[j] <= trigger and y[j-1] > trigger and index > -1 and len(pairs[index]) == 1:
					pairs[index].append(x[j])

			# Generate a list of tuples containing the starting offset to begin analysis plus a length
			for pair in pairs:
				start = pair[0]
				if len(pair) == 2:
					stop = pair[1]
				else:
					self.fd.seek(0, 2)
					stop = self.fd.tell()

				length = stop - start
				total += length
				scan_pairs.append((start, length))

			# Update the binwalk scan length and total scanned values so that the percent complete
			# isn't stuck at 100% after the initial entropy analysis (which has already finished).
			if self.binwalk and total > 0:
				self.binwalk.scan_length = total
				self.binwalk.total_scanned = 0

			# Analyze each scan pair and display the results
			for (start, length) in scan_pairs:
				# Ignore anything less than 4KB in size
				if length > (self.DEFAULT_BLOCK_SIZE * 4):
					# Ignore the first and last 1KB of data to prevent header/footer or extra data from skewing results
					result = compression.CompressionEntropyAnalyzer(self.fd.name, start+self.DEFAULT_BLOCK_SIZE, length-self.DEFAULT_BLOCK_SIZE).analyze()
					results = [{'description' : result[0]['description'], 'offset' : start}]
	
					self.file_results.append((start, results))
					if self.binwalk:
						self.binwalk.display.results(start, results)

				# Keep the total scanned length updated
				if self.binwalk:
					self.binwalk.total_scanned += length

	def analyze(self, algorithm=None):
		'''
		Performs an entropy analysis of the data using the specified algorithm.

		@algorithm - A method inside of the Entropy class to invoke for entropy analysis.
			     Default method: self.shannon.
			     Other available methods: self.gzip.
			     May also be a string: 'gzip'.

		Returns the return value of algorithm.
		'''
		algo = self.shannon

		if algorithm:
			if callable(algorithm):
				algo = algorithm

			try:
				if algorithm.lower() == 'gzip':
					algo = self.gzip
			except:
				pass

		return self._do_analysis(algo)
	
	def plot(self, x, y, average=0, show_legend=True, save=False):
		'''
		Plots entropy data.

		@x            - List of graph x-coordinates (i.e., data offsets).
		@y            - List of graph y-coordinates (i.e., entropy for each offset).
		@average      - The average entropy.
		@show_legend  - Set to False to not generate a color-coded legend and plotted x coordinates for the graph.
		@save         - If set to True, graph will be saved to disk rather than displayed.

		Returns None.
		'''
		PlotEntropy(x, y, self.fd.name, average, self.file_results, show_legend, save)

class Entropy(object):
	'''
	Class for analyzing and plotting data entropy for multiple files.

	A simple example of performing a binwalk scan and overlaying the binwalk scan results on the
	resulting entropy analysis graph:

		import sys
		import binwalk

		bwalk = binwalk.Binwalk()
		scan_results = bwalk.scan(sys.argv[1])

                with binwalk.entropy.Entropy(scan_results, bwalk) as e:
                        e.analyze()

		bwalk.cleanup()
	'''

	DESCRIPTION = "ENTROPY ANALYSIS"
	ALT_DESCRIPTION = "HEURISTIC ANALYSIS"
	ENTROPY_SCAN = 'entropy'

	def __init__(self, files, binwalk=None, offset=0, length=0, block=0, plot=True, legend=True, save=False, algorithm=None, load_plugins=True, whitelist=[], blacklist=[], compcheck=False):
		'''
		Class constructor.

		@files        - A dictionary containing file names and results data, as returned by Binwalk.scan.
		@binwalk      - An instance of the Binwalk class.
		@offset       - The offset into the data to begin analysis.
		@length       - The number of bytes to analyze.
		@block        - The size of the data blocks to analyze.
		@plot         - Set to False to disable plotting.
		@legend       - Set to False to exclude the legend and custom offset markers from the plot.
		@save         - Set to True to save plots to disk instead of displaying them.
		@algorithm    - Set to 'gzip' to use the gzip entropy "algorithm".
		@load_plugins - Set to False to disable plugin callbacks.
		@whitelist    - A list of whitelisted plugins.
		@blacklist    - A list of blacklisted plugins.
		@compcheck    - Set to True to enable entropy compression detection.

		Returns None.
		'''
		self.files = files
		self.binwalk = binwalk
		self.offset = offset
		self.length = length
		self.block = block
		self.plot = plot
		self.legend = legend
		self.save = save
		self.algorithm = algorithm
		self.plugins = None
		self.load_plugins = load_plugins
		self.whitelist = whitelist
		self.blacklist = blacklist
		self.compcheck = compcheck

		if len(self.files) > 1:
			self.save = True

		if self.binwalk:
			self.binwalk.scan_type = self.binwalk.ENTROPY

	def __enter__(self):
		return self

	def __exit__(self, t, v, traceback):
		return None

	def __del__(self):
		return None

	def set_entropy_algorithm(self, algorithm):
		'''
		Specify a function/method to call for determining data entropy.

		@algorithm - The function/method to call. This will be  passed two arguments:
			     the file offset of the data block, and a data block (type 'str').
		             It must return a single floating point entropy value from 0.0 and 1.0, inclusive.

		Returns None.
		'''
		self.algorithm = algorithm

	def analyze(self):
		'''
		Perform an entropy analysis on the target files.

		Returns a dictionary of:
			
			{
				'file_name' : ([list, of, offsets], [list, of, entropy], average_entropy)
			}
		'''
		results = {}

		if self.binwalk and self.load_plugins:
			self.plugins = plugins.Plugins(self.binwalk, whitelist=self.whitelist, blacklist=self.blacklist)

		for (file_name, overlay) in iterator(self.files):

			if self.plugins:
				self.plugins._load_plugins()

			if self.binwalk:
				if self.compcheck:
					desc = self.ALT_DESCRIPTION
				else:
					desc = self.DESCRIPTION

				self.binwalk.display.header(file_name=file_name, description=desc)

			with FileEntropy(file_name=file_name, binwalk=self.binwalk, offset=self.offset, length=self.length, block=self.block, plugins=self.plugins, file_results=overlay, compcheck=self.compcheck) as e:
				(x, y, average) = e.analyze(self.algorithm)
				
				if self.plot or self.save:
					e.plot(x, y, average, self.legend, self.save)
				
				results[file_name] = (x, y, average)

			if self.binwalk:
				self.binwalk.display.footer()

		if self.plugins:
			del self.plugins
			self.plugins = None

		return results

