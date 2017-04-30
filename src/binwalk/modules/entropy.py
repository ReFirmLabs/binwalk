# Calculates and optionally plots the entropy of input files.

import os
import math
import zlib
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

    DEFAULT_BLOCK_SIZE = 1024
    DEFAULT_DATA_POINTS = 2048

    DEFAULT_TRIGGER_HIGH = .95
    DEFAULT_TRIGGER_LOW = .85

    TITLE = "Entropy Analysis"
    ORDER = 8

    # TODO: Add --dpoints option to set the number of data points?
    CLI = [
        Option(short='E',
               long='entropy',
               kwargs={'enabled': True},
               description='Calculate file entropy'),
        Option(short='F',
               long='fast',
               kwargs={'use_zlib': True},
               description='Use faster, but less detailed, entropy analysis'),
        Option(short='J',
               long='save',
               kwargs={'save_plot': True},
               description='Save plot as a PNG'),
        Option(short='Q',
               long='nlegend',
               kwargs={'show_legend': False},
               description='Omit the legend from the entropy plot graph'),
        Option(short='N',
               long='nplot',
               kwargs={'do_plot': False},
               description='Do not generate an entropy plot graph'),
        Option(short='H',
               long='high',
               type=float,
               kwargs={'trigger_high': DEFAULT_TRIGGER_HIGH},
               description='Set the rising edge entropy trigger threshold (default: %.2f)' % DEFAULT_TRIGGER_HIGH),
        Option(short='L',
               long='low',
               type=float,
               kwargs={'trigger_low': DEFAULT_TRIGGER_LOW},
               description='Set the falling edge entropy trigger threshold (default: %.2f)' % DEFAULT_TRIGGER_LOW),
    ]

    KWARGS = [
        Kwarg(name='enabled', default=False),
        Kwarg(name='save_plot', default=False),
        Kwarg(name='trigger_high', default=DEFAULT_TRIGGER_HIGH),
        Kwarg(name='trigger_low', default=DEFAULT_TRIGGER_LOW),
        Kwarg(name='use_zlib', default=False),
        Kwarg(name='display_results', default=True),
        Kwarg(name='do_plot', default=True),
        Kwarg(name='show_legend', default=True),
        Kwarg(name='block_size', default=0),
    ]

    # Run this module last so that it can process all other module's results
    # and overlay them on the entropy graph
    PRIORITY = 0

    def init(self):
        self.HEADER[-1] = "ENTROPY"
        self.max_description_length = 0
        self.file_markers = {}

        if self.use_zlib:
            self.algorithm = self.gzip
        else:
            self.algorithm = self.shannon

        # Get a list of all other module's results to mark on the entropy graph
        for (module, obj) in iterator(self.modules):
            for result in obj.results:
                if result.plot and result.file and result.description:
                    description = result.description.split(',')[0]

                    if not has_key(self.file_markers, result.file.name):
                        self.file_markers[result.file.name] = []

                    if len(description) > self.max_description_length:
                        self.max_description_length = len(description)

                    self.file_markers[result.file.name].append(
                        (result.offset, description))

        # If other modules have been run and they produced results, don't spam
        # the terminal with entropy results
        if self.file_markers:
            self.display_results = False

        if not self.block_size:
            if self.config.block:
                self.block_size = self.config.block
            else:
                self.block_size = None

    def _entropy_sigterm_handler(self, *args):
        print ("FUck it all.")

    def run(self):
        # If generating a graphical plot, this function will never return, as it invokes
        # pg.exit. Calling pg.exit is pretty much required, but pg.exit calls os._exit in
        # order to work around QT cleanup issues.
        self._run()

    def _run(self):
        # Sanity check and warning if pyqtgraph isn't found
        if self.do_plot:
            try:
                import pyqtgraph as pg
            except ImportError as e:
                binwalk.core.common.warning(
                    "Failed to import pyqtgraph module, visual entropy graphing will be disabled")
                self.do_plot = False

        for fp in iter(self.next_file, None):

            if self.display_results:
                self.header()

            self.calculate_file_entropy(fp)

            if self.display_results:
                self.footer()

        if self.do_plot:
            if not self.save_plot:
                from pyqtgraph.Qt import QtGui
                QtGui.QApplication.instance().exec_()
            pg.exit()

    def calculate_file_entropy(self, fp):
        # Tracks the last displayed rising/falling edge (0 for falling, 1 for
        # rising, None if nothing has been printed yet)
        last_edge = None
        # Auto-reset the trigger; if True, an entropy above/below
        # self.trigger_high/self.trigger_low will be printed
        trigger_reset = True

        # Clear results from any previously analyzed files
        self.clear(results=True)

        # If -K was not specified, calculate the block size to create
        # DEFAULT_DATA_POINTS data points
        if self.block_size is None:
            block_size = fp.size / self.DEFAULT_DATA_POINTS
            # Round up to the nearest DEFAULT_BLOCK_SIZE (1024)
            block_size = int(block_size +
                             ((self.DEFAULT_BLOCK_SIZE -
                               block_size) %
                              self.DEFAULT_BLOCK_SIZE))
        else:
            block_size = self.block_size

        # Make sure block size is greater than 0
        if block_size <= 0:
            block_size = self.DEFAULT_BLOCK_SIZE

        binwalk.core.common.debug("Entropy block size (%d data points): %d" % (
            self.DEFAULT_DATA_POINTS, block_size))

        while True:
            file_offset = fp.tell()

            (data, dlen) = fp.read_block()
            if not data:
                break

            i = 0
            while i < dlen:
                entropy = self.algorithm(data[i:i + block_size])
                display = self.display_results
                description = "%f" % entropy

                if not self.config.verbose:
                    if last_edge in [None, 0] and entropy > self.trigger_low:
                        trigger_reset = True
                    elif last_edge in [None, 1] and entropy < self.trigger_high:
                        trigger_reset = True

                    if trigger_reset and entropy >= self.trigger_high:
                        description = "Rising entropy edge (%f)" % entropy
                        display = self.display_results
                        last_edge = 1
                        trigger_reset = False
                    elif trigger_reset and entropy <= self.trigger_low:
                        description = "Falling entropy edge (%f)" % entropy
                        display = self.display_results
                        last_edge = 0
                        trigger_reset = False
                    else:
                        display = False
                        description = "%f" % entropy

                r = self.result(offset=(file_offset + i),
                                file=fp,
                                entropy=entropy,
                                description=description,
                                display=display)

                i += block_size

        if self.do_plot:
            self.plot_entropy(fp.name)

    def shannon(self, data):
        '''
        Performs a Shannon entropy analysis on a given block of data.
        '''
        entropy = 0

        if data:
            length = len(data)

            seen = dict(((chr(x), 0) for x in range(0, 256)))
            for byte in data:
                seen[byte] += 1

            for x in range(0, 256):
                p_x = float(seen[chr(x)]) / length
                if p_x > 0:
                    entropy -= p_x * math.log(p_x, 2)

        return (entropy / 8)

    def gzip(self, data, truncate=True):
        '''
        Performs an entropy analysis based on zlib compression ratio.
        This is faster than the shannon entropy analysis, but not as accurate.
        '''
        # Entropy is a simple ratio of: <zlib compressed size> / <original
        # size>
        e = float(float(len(zlib.compress(str2bytes(data), 9))) /
                  float(len(data)))

        if truncate and e > 1.0:
            e = 1.0

        return e

    def plot_entropy(self, fname):
        try:
            import numpy as np
            import pyqtgraph as pg
            import pyqtgraph.exporters as exporters
        except ImportError as e:
            return

        i = 0
        x = []
        y = []
        plotted_colors = {}

        for r in self.results:
            x.append(r.offset)
            y.append(r.entropy)

        plt = pg.plot(title=fname, clear=True)

        # Disable auto-ranging of the Y (entropy) axis, as it
        # can cause some very un-intuitive graphs, particularly
        # for files with only high-entropy data.
        plt.setYRange(0, 1)

        if self.show_legend and has_key(self.file_markers, fname):
            plt.addLegend(size=(self.max_description_length * 10, 0))

            for (offset, description) in self.file_markers[fname]:
                # If this description has already been plotted at a different offset, we need to
                # use the same color for the marker, but set the description to None to prevent
                # duplicate entries in the graph legend.
                #
                # Else, get the next color and use it to mark descriptions of
                # this type.
                if has_key(plotted_colors, description):
                    color = plotted_colors[description]
                    description = None
                else:
                    color = self.COLORS[i]
                    plotted_colors[description] = color

                    i += 1
                    if i >= len(self.COLORS):
                        i = 0

                plt.plot(x=[offset, offset], y=[0, 1.1],
                         name=description, pen=pg.mkPen(color, width=2.5))

        # Plot data points
        plt.plot(x, y, pen='y')

        # TODO: legend is not displayed properly when saving plots to disk
        if self.save_plot:
            # Save graph to CWD
            out_file = os.path.join(os.getcwd(), os.path.basename(fname))

            # exporters.ImageExporter is different in different versions of
            # pyqtgraph
            try:
                exporter = exporters.ImageExporter(plt.plotItem)
            except TypeError:
                exporter = exporters.ImageExporter.ImageExporter(plt.plotItem)
            exporter.parameters()['width'] = self.FILE_WIDTH
            exporter.export(binwalk.core.common.unique_file_name(
                out_file, self.FILE_FORMAT))
        else:
            plt.setLabel('left', self.YLABEL, units=self.YUNITS)
            plt.setLabel('bottom', self.XLABEL, units=self.XUNITS)
