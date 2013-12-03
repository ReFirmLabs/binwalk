import os
from binwalk.compat import *
from binwalk.common import BlockFile

class Plotter(object):

	DIMENSIONS = 3
	VIEW_DISTANCE = 1024

	def __init__(self, files, offset=0, length=0, weight=None, show_grids=False, verbose=False):
		import pyqtgraph.opengl as gl
		from pyqtgraph.Qt import QtGui

		self.verbose = verbose
		self.show_grids = show_grids
		self.files = files
		self.weight = weight
		self.offset = offset
		self.length = length

		self.app = QtGui.QApplication([])
		self.window = gl.GLViewWidget()
		self.window.opts['distance'] = self.VIEW_DISTANCE
		
		if len(self.files) == 1:
			self.window.setWindowTitle(self.files[0])

	def _print(self, message):
		if self.verbose:
			print (message)

	def _generate_plot_points(self, data_points, data_weights):
		plot_points = set()
		max_plot_points = (24 * 1024)

		if self.weight:
			weight = self.weight
		else:
			self._print("Calculating weight...")

			weight = 1

			if len(data_points) > max_plot_points:
				weightings = {}

				for i in range(1, 11):
					weightings[i] = 0

				for point in data_points:
					for w in get_keys(weightings):
						if data_weights[point] >= w:
							weightings[w] += 1
					
						if weightings[w] > max_plot_points:
							del weightings[w]

					if len(weightings) <= 1:
						break

				if weightings:
					weight = min(weightings)

		self._print("Weight: %d" % weight)

		for point in data_points:
			if data_weights[point] >= weight:
				plot_points.add(point)
			
		return plot_points

	def _generate_data_point(self, data):
		return (0,0,0)

	def _generate_data_points(self, file_name):
		i = 0
		data_weights = {}
		data_points = set()

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
					if point in data_points:	
						data_weights[point] += 1
					else:
						data_points.add(point)
						data_weights[point] = 1
					i += 3

		return (data_points, data_weights)

	def _generate_plot(self, plot_points, point_weights):
		import numpy as np
		import pyqtgraph.opengl as gl
		
		nitems = len(plot_points)

		pos = np.empty((nitems, 3))
		size = np.empty((nitems))
		color = np.empty((nitems, 4))

		i = 0
		for point in plot_points:
			r = 0.0
			g = 0.0
			b = 0.0

			pos[i] = point
			size[i] = .05

			if point_weights[point] > 15:
				r = 1.0
			elif point_weights[point] > 5:
				g = 1.0
				r = 1.0
			else:
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
			(data_points, data_weights) = self._generate_data_points(file_name)

			self._print("Generating plot points from %d data points" % len(data_points))

			plot_points = self._generate_plot_points(data_points, data_weights)

			self._print("Generating graph from %d plot points" % len(plot_points))

			self.window.addItem(self._generate_plot(plot_points, data_weights))

		if wait:
			self.wait()

	def wait(self):
		from pyqtgraph.Qt import QtCore, QtGui

		t = QtCore.QTimer()
		t.start(50)
		QtGui.QApplication.instance().exec_()


class Plotter3D(Plotter):

	DIMENSIONS = 3

	def _generate_data_point(self, data):
		return (ord(data[0]), ord(data[1]), ord(data[2]))
	
class Plotter2D(Plotter):
	'''
	This is of questionable use.
	'''

	DIMENSIONS = 2
	plane_count = -1

	def _generate_data_point(self, data):
		self.plane_count += 1
		if self.plane_count > 2:
			self.plane_count = 0

		if self.plane_count == 0:
			return (0, ord(data[0]), ord(data[1]))
		elif self.plane_count == 1:
			return (ord(data[0]), 0, ord(data[1]))
		elif self.plane_count == 2:
			return (ord(data[0]), ord(data[1]), 0)
		
if __name__ == '__main__':
	import sys
	
	try:
		weight = int(sys.argv[2])
	except:
		weight = None

	Plotter3D(sys.argv[1:], weight=weight, verbose=True).plot()

