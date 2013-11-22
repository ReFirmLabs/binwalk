import os
from binwalk.compat import *
from binwalk.common import BlockFile

class Plotter(object):
	'''
	Base class for plotting binaries in Qt.
	Other plotter classes are derived from this.
	'''

	DIMENSIONS = 3
	VIEW_DISTANCE = 1024
	MAX_PLOT_POINTS = 25000

	def __init__(self, files, offset=0, length=0, max_points=MAX_PLOT_POINTS, show_grids=False, verbose=False):
		'''
		Class constructor.

		@files      - A list of files to plot in the graph.
		@offset     - The starting offset for each file.
		@length     - The number of bytes to analyze from each file.
		@max_points - The maximum number of data points to display.
		@show_grids - Set to True to display x-y-z grids.
		@verbse     - Set to False to disable verbose print statements.

		Returns None.
		'''
		import pyqtgraph.opengl as gl
		from pyqtgraph.Qt import QtGui

		self.verbose = verbose
		self.show_grids = show_grids
		self.files = files
		self.offset = offset
		self.length = length
	
		if not max_points:
			self.max_points = self.MAX_PLOT_POINTS
		else:
			self.max_points = max_points

		self.app = QtGui.QApplication([])
		self.window = gl.GLViewWidget()
		self.window.opts['distance'] = self.VIEW_DISTANCE
		
		if len(self.files) == 1:
			self.window.setWindowTitle(self.files[0])

	def _print(self, message):
		'''
		Print console messages. For internal use only.
		'''
		if self.verbose:
			print (message)

	def _generate_plot_points(self, data_points):
		'''
		Generates plot points from a list of data points.
		
		@data_points - A dictionary containing each unique point and its frequency of occurance.

		Returns a set of plot points.
		'''
		total = 0
		min_weight = 0
		weightings = {}
		plot_points = {}

		# If the number of data points exceeds the maximum number of allowed data points, use a
		# weighting system to eliminate data points that occur less freqently.
		if sum(data_points.itervalues()) > self.max_points:

			# First, generate a set of weight values 1 - 10
			for i in range(1, 11):
				weightings[i] = 0

			# Go through every data point and how many times that point occurs
			for (point, count) in iterator(data_points):
				# For each data point, compare it to each remaining weight value
				for w in get_keys(weightings):

					# If the number of times this data point occurred is >= the weight value,
					# then increment the weight value. Since weight values are ordered lowest
					# to highest, this means that more frequent data points also increment lower
					# weight values. Thus, the more high-frequency data points there are, the
					# more lower-frequency data points are eliminated.
					if count >= w:
						weightings[w] += 1
					else:
						break

					# Throw out weight values that exceed the maximum number of data points
					if weightings[w] > self.max_points:
						del weightings[w]

				# If there's only one weight value left, no sense in continuing the loop...
				if len(weightings) == 1:
					break

			# The least weighted value is our minimum weight
			min_weight = min(weightings)

			# Get rid of all data points that occur less frequently than our minimum weight
			for point in get_keys(data_points):
				if data_points[point] < min_weight:
					del data_points[point]

		for point in sorted(data_points, key=data_points.get, reverse=True):
			plot_points[point] = data_points[point]
			total += 1
			if total >= self.max_points:
				break
					
		return plot_points

	def _generate_data_point(self, data):
		'''
		Subclasses must override this to return the appropriate data point.

		@data - A string of data self.DIMENSIONS in length.

		Returns a data point tuple.
		'''
		return (0,0,0)

	def _generate_data_points(self, file_name):
		'''
		Generates a dictionary of data points and their frequency of occurrance.

		@file_name - The file to generate data points from.

		Returns a dictionary.
		'''
		i = 0
		data_points = {}

		self._print("Generating data points for %s" % file_name)

		with BlockFile(file_name, 'r', offset=self.offset, length=self.length) as fp:
			fp.MAX_TRAILING_SIZE = 0

			while True:
				(data, dlen) = fp.read_block()
				if not data or not dlen:
					break

				i = 0
				while (i+(self.DIMENSIONS-1)) < dlen:
					point = self._generate_data_point(data[i:i+self.DIMENSIONS])
					if has_key(data_points, point):	
						data_points[point] += 1
					else:
						data_points[point] = 1
					i += 3

		return data_points

	def _generate_plot(self, plot_points):
		import numpy as np
		import pyqtgraph.opengl as gl
		
		nitems = float(len(plot_points))

		pos = np.empty((nitems, 3))
		size = np.empty((nitems))
		color = np.empty((nitems, 4))

		i = 0
		for (point, weight) in iterator(plot_points):
			r = 0.0
			g = 0.0
			b = 0.0

			pos[i] = point
			frequency_percentage = (weight / nitems)

			# Give points that occur more frequently a brighter color and larger point size.
			# Frequency is determined as a percentage of total unique data points.
			if frequency_percentage > .005:
				size[i] = .20
				r = 1.0
			elif frequency_percentage > .002:
				size[i] = .10
				g = 1.0
				r = 1.0
			else:
				size[i] = .05
				g = 1.0

			color[i] = (r, g, b, 1.0)

			i += 1

		scatter_plot = gl.GLScatterPlotItem(pos=pos, size=size, color=color, pxMode=False)
		scatter_plot.translate(-127.5, -127.5, -127.5)

		return scatter_plot

	def plot(self, wait=True):
		import pyqtgraph.opengl as gl

		self.window.show()

		if self.show_grids:
			xgrid = gl.GLGridItem()
			ygrid = gl.GLGridItem()
			zgrid = gl.GLGridItem()

			self.window.addItem(xgrid)
			self.window.addItem(ygrid)
			self.window.addItem(zgrid)

			# Rotate x and y grids to face the correct direction
			xgrid.rotate(90, 0, 1, 0)
			ygrid.rotate(90, 1, 0, 0)

			# Scale grids to the appropriate dimensions
			xgrid.scale(12.8, 12.8, 12.8)
			ygrid.scale(12.8, 12.8, 12.8)
			zgrid.scale(12.8, 12.8, 12.8)

		for file_name in self.files:
			data_points = self._generate_data_points(file_name)

			self._print("Generating plot points from %d data points" % len(data_points))

			plot_points = self._generate_plot_points(data_points)
			del data_points

			self._print("Generating graph from %d plot points" % len(plot_points))

			self.window.addItem(self._generate_plot(plot_points))

		if wait:
			self.wait()

	def wait(self):
		from pyqtgraph.Qt import QtCore, QtGui

		t = QtCore.QTimer()
		t.start(50)
		QtGui.QApplication.instance().exec_()


class Plotter3D(Plotter):
	'''
	Plot data points within a 3D cube.
	'''
	DIMENSIONS = 3

	def _generate_data_point(self, data):
		return (ord(data[0]), ord(data[1]), ord(data[2]))
	
class Plotter2D(Plotter):
	'''
	Plot data points projected on each cube face.
	'''

	DIMENSIONS = 2
	MAX_PLOT_POINTS = 12500
	plane_count = -1

	def _generate_data_point(self, data):
		self.plane_count += 1
		if self.plane_count > 5:
			self.plane_count = 0

		if self.plane_count == 0:
			return (0, ord(data[0]), ord(data[1]))
		elif self.plane_count == 1:
			return (ord(data[0]), 0, ord(data[1]))
		elif self.plane_count == 2:
			return (ord(data[0]), ord(data[1]), 0)
		elif self.plane_count == 3:
			return (255, ord(data[0]), ord(data[1]))
		elif self.plane_count == 4:
			return (ord(data[0]), 255, ord(data[1]))
		elif self.plane_count == 5:
			return (ord(data[0]), ord(data[1]), 255)
		
if __name__ == '__main__':
	import sys
	
	try:
		weight = int(sys.argv[2])
	except:
		weight = None

	Plotter2D(sys.argv[1:], weight=weight, verbose=True).plot()

