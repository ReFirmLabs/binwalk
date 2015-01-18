# Generates 3D visualizations of input files.

import os
from binwalk.core.compat import *
from binwalk.core.common import BlockFile
from binwalk.core.module import Module, Option, Kwarg

class Plotter(Module):
    '''
    Base class for visualizing binaries in Qt.
    Other plotter classes are derived from this.
    '''
    VIEW_DISTANCE = 1024
    MAX_2D_PLOT_POINTS = 12500
    MAX_3D_PLOT_POINTS = 25000

    TITLE = "Binary Visualization"

    CLI = [
            Option(short='3',
                   long='3D',
                   kwargs={'axis' : 3, 'enabled' : True},
                   description='Generate a 3D binary visualization'),
            Option(short='2',
                   long='2D',
                   kwargs={'axis' : 2, 'enabled' : True},
                   description='Project data points onto 3D cube walls only'),
            Option(short='Z',
                   long='points',
                   type=int,
                   kwargs={'max_points' : 0},
                   description='Set the maximum number of plotted data points'),
#            Option(short='V',
#                   long='grids',
#                   kwargs={'show_grids' : True},
#                   description='Display the x-y-z grids in the resulting plot'),
    ]

    KWARGS = [
            Kwarg(name='axis', default=3),
            Kwarg(name='max_points', default=0),
            Kwarg(name='show_grids', default=False),
            Kwarg(name='enabled', default=False),
    ]

    # There isn't really any useful data to print to console. Disable header and result output.
    HEADER = None
    RESULT = None

    def init(self):
        import pyqtgraph.opengl as gl
        from pyqtgraph.Qt import QtGui

        self.verbose = self.config.verbose
        self.offset = self.config.offset
        self.length = self.config.length
        self.plane_count = -1
        self.plot_points = None

        if self.axis == 2:
            self.MAX_PLOT_POINTS = self.MAX_2D_PLOT_POINTS
            self._generate_data_point = self._generate_2d_data_point
        elif self.axis == 3:
            self.MAX_PLOT_POINTS = self.MAX_3D_PLOT_POINTS
            self._generate_data_point = self._generate_3d_data_point
        else:
            raise Exception("Invalid Plotter axis specified: %d. Must be one of: [2,3]" % self.axis)

        if not self.max_points:
            self.max_points = self.MAX_PLOT_POINTS

        self.app = QtGui.QApplication([])
        self.window = gl.GLViewWidget()
        self.window.opts['distance'] = self.VIEW_DISTANCE

        if len(self.config.target_files) == 1:
            self.window.setWindowTitle(self.config.target_files[0])

    def _print(self, message):
        '''
        Print console messages. For internal use only.
        '''
        if self.verbose:
            print(message)

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
        if sum(data_points.values()) > self.max_points:

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
            # Register this as a result in case future modules need access to the raw point information,
            # but mark plot as False to prevent the entropy module from attempting to overlay this data on its graph.
            self.result(point=point, plot=False)
            total += 1
            if total >= self.max_points:
                break

        return plot_points

    def _generate_data_point(self, data):
        '''
        Subclasses must override this to return the appropriate data point.

        @data - A string of data self.axis in length.

        Returns a data point tuple.
        '''
        return (0,0,0)

    def _generate_data_points(self, fp):
        '''
        Generates a dictionary of data points and their frequency of occurrance.

        @fp - The BlockFile object to generate data points from.

        Returns a dictionary.
        '''
        i = 0
        data_points = {}

        self._print("Generating data points for %s" % fp.name)

        # We don't need any extra data from BlockFile
        fp.set_block_size(peek=0)

        while True:
            (data, dlen) = fp.read_block()
            if not data or not dlen:
                break

            i = 0
            while (i+(self.axis-1)) < dlen:
                point = self._generate_data_point(data[i:i+self.axis])
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
            if frequency_percentage > .010:
                size[i] = .20
                r = 1.0
            elif frequency_percentage > .005:
                size[i] = .15
                b = 1.0
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

        for fd in iter(self.next_file, None):
            data_points = self._generate_data_points(fd)

            self._print("Generating plot points from %d data points" % len(data_points))

            self.plot_points = self._generate_plot_points(data_points)
            del data_points

            self._print("Generating graph from %d plot points" % len(self.plot_points))

            self.window.addItem(self._generate_plot(self.plot_points))

        if wait:
            self.wait()

    def wait(self):
        from pyqtgraph.Qt import QtCore, QtGui

        t = QtCore.QTimer()
        t.start(50)
        QtGui.QApplication.instance().exec_()

    def _generate_3d_data_point(self, data):
        '''
        Plot data points within a 3D cube.
        '''
        return (ord(data[0]), ord(data[1]), ord(data[2]))

    def _generate_2d_data_point(self, data):
        '''
        Plot data points projected on each cube face.
        '''
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

    def run(self):
        self.plot()
        return True

