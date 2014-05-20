# Calculates and optionally plots the entropy of input files.

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

    DEFAULT_BLOCK_SIZE = 1024

    TITLE = "Entropy Analysis"
    ORDER = 8
    
    CLI = [
            Option(short='E',
                   long='entropy',
                   kwargs={'enabled' : True},
                   description='Calculate file entropy'),
            Option(short='J',
                   long='save',
                   kwargs={'save_plot' : True},
                   description='Save plot as a PNG'),
            Option(short='N',
                   long='nplot',
                   kwargs={'do_plot' : False},
                   description='Do not generate an entropy plot graph'),
            Option(short='Q',
                   long='nlegend',
                   kwargs={'show_legend' : False},
                   description='Omit the legend from the entropy plot graph'),
    ]

    KWARGS = [
            Kwarg(name='enabled', default=False),
            Kwarg(name='save_plot', default=False),
            Kwarg(name='display_results', default=True),
            Kwarg(name='do_plot', default=True),
            Kwarg(name='show_legend', default=True),
            Kwarg(name='block_size', default=0),
    ]

    # Run this module last so that it can process all other module's results and overlay them on the entropy graph
    PRIORITY = 0

    def init(self):
        self.HEADER[-1] = "ENTROPY"
        self.algorithm = self.shannon
        self.max_description_length = 0
        self.file_markers = {}

        # Get a list of all other module's results to mark on the entropy graph
        for (module, obj) in iterator(self.modules):
            for result in obj.results:
                if result.plot and result.file and result.description:
                    description = result.description.split(',')[0]

                    if not has_key(self.file_markers, result.file.name):
                        self.file_markers[result.file.name] = []

                    if len(description) > self.max_description_length:
                        self.max_description_length = len(description)

                    self.file_markers[result.file.name].append((result.offset, description))

        # If other modules have been run and they produced results, don't spam the terminal with entropy results
        if self.file_markers:
            self.display_results = False

        if not self.block_size:
            if self.config.block:
                self.block_size = self.config.block
            else:
                self.block_size = self.DEFAULT_BLOCK_SIZE

    def run(self):
        for fp in iter(self.next_file, None):

            if self.display_results:
                self.header()

            self.calculate_file_entropy(fp)

            if self.display_results:
                self.footer()
    
        if self.do_plot and not self.save_plot:    
            from pyqtgraph.Qt import QtGui
            QtGui.QApplication.instance().exec_()

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
            length = len(data)
            
            seen = dict(((chr(x), 0) for x in range(0, 256)))
            for byte in data:
                seen[byte] += 1

            for x in range(0, 256):
                p_x = float(seen[chr(x)]) / length
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
        import pyqtgraph.exporters as exporters

        i = 0
        x = []
        y = []
        plotted_colors = {}

        for r in self.results:
            x.append(r.offset)
            y.append(r.entropy)

        plt = pg.plot(title=fname, clear=True)

        if self.show_legend and has_key(self.file_markers, fname):
            plt.addLegend(size=(self.max_description_length*10, 0))

            for (offset, description) in self.file_markers[fname]:
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

        # Plot data points
        plt.plot(x, y, pen='y')

        # TODO: legend is not displayed properly when saving plots to disk
        if self.save_plot:
            exporter = exporters.ImageExporter.ImageExporter(plt.plotItem)
            exporter.parameters()['width'] = self.FILE_WIDTH
            exporter.export(binwalk.core.common.unique_file_name(os.path.basename(fname), self.FILE_FORMAT))
        else:
            plt.setLabel('left', self.YLABEL, units=self.YUNITS)
            plt.setLabel('bottom', self.XLABEL, units=self.XUNITS)

