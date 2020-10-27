# Calculates and optionally plots the entropy of input files.

import os
import sys
import math
import zlib
import binwalk.core.common
from binwalk.core.compat import *
from binwalk.core.module import Module, Option, Kwarg

#try:
#    import numpy as np
#except ImportError:
#    pass
try:
    from numba import njit
except ImportError:
    def njit(func):
        return func

class Entropy(Module):

    XLABEL = 'Offset'
    YLABEL = 'Entropy'

    XUNITS = 'B'
    YUNITS = 'E'

    FILE_WIDTH = 1024
    FILE_FORMAT = 'png'

    COLORS = ['g', 'r', 'c', 'm', 'y']

    DEFAULT_BLOCK_SIZE = 1024
    DEFAULT_DATA_POINTS = 2048

    DEFAULT_TRIGGER_HIGH = .95
    DEFAULT_TRIGGER_LOW = .85

    TITLE = "Entropy"
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
        self.output_file = None

        if self.use_zlib:
            self.algorithm = self.gzip
        else:
            if 'numpy' in sys.modules:
                self.algorithm = self.shannon_numpy
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

                    self.file_markers[result.file.name].append((result.offset, description))

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
        print ("Fuck it all.")

    def run(self):
        self._run()

    def _run(self):
        # Sanity check and warning if matplotlib isn't found
        if self.do_plot:
            try:
                # If we're saving the plot to a file, configure matplotlib
                # to use the Agg back-end. This does not require a X server,
                # allowing users to generate plot files on headless systems.
                if self.save_plot:
                    import matplotlib as mpl
                    mpl.use('Agg')
                import matplotlib.pyplot as plt
            except ImportError as e:
                binwalk.core.common.warning("Failed to import matplotlib module, visual entropy graphing will be disabled")
                self.do_plot = False

        for fp in iter(self.next_file, None):

            if self.display_results:
                self.header()

            self.calculate_file_entropy(fp)

            if self.display_results:
                self.footer()

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
            block_size = int(block_size + ((self.DEFAULT_BLOCK_SIZE - block_size) % self.DEFAULT_BLOCK_SIZE))
        else:
            block_size = self.block_size

        # Make sure block size is greater than 0
        if block_size <= 0:
            block_size = self.DEFAULT_BLOCK_SIZE

        binwalk.core.common.debug("Entropy block size (%d data points): %d" %
                                  (self.DEFAULT_DATA_POINTS, block_size))

        while True:
            file_offset = fp.tell()

            (data, dlen) = fp.read_block()
            if dlen < 1:
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

    def shannon_numpy(self, data):
        if data:
            return self._shannon_numpy(bytes2str(data))
        else:
            return 0
    
    @staticmethod
    @njit
    def _shannon_numpy(data):
            A = np.frombuffer(data, dtype=np.uint8)
            pA = np.bincount(A) / len(A)
            entropy = -np.nansum(pA*np.log2(pA))
            return (entropy / 8)

    def gzip(self, data, truncate=True):
        '''
        Performs an entropy analysis based on zlib compression ratio.
        This is faster than the shannon entropy analysis, but not as accurate.
        '''
        # Entropy is a simple ratio of: <zlib compressed size> / <original
        # size>
        e = float(float(len(zlib.compress(str2bytes(data), 9))) / float(len(data)))

        if truncate and e > 1.0:
            e = 1.0

        return e

    def plot_entropy(self, fname):
        try:
            import matplotlib.pyplot as plt
        except ImportError as e:
            return

        i = 0
        x = []
        y = []
        plotted_colors = {}

        for r in self.results:
            x.append(r.offset)
            y.append(r.entropy)

        fig = plt.figure()

        # axisbg is depreciated, but older versions of matplotlib don't support facecolor.
        # This tries facecolor first, thus preventing the annoying depreciation warnings,
        # and falls back to axisbg if that fails.
        try:
            ax = fig.add_subplot(1, 1, 1, autoscale_on=True, facecolor='black')
        except AttributeError:
            ax = fig.add_subplot(1, 1, 1, autoscale_on=True, axisbg='black')

        ax.set_title(self.TITLE)
        ax.set_xlabel(self.XLABEL)
        ax.set_ylabel(self.YLABEL)
        ax.plot(x, y, 'y', lw=2)

        # Add a fake, invisible plot entry so that offsets at/near the
        # minimum x value (0) are actually visible on the plot.
        ax.plot(-(max(x)*.001), 1.1, lw=0)
        ax.plot(-(max(x)*.001), 0, lw=0)

        if self.show_legend and has_key(self.file_markers, fname):
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

                ax.plot([offset, offset], [0, 1.1], '%s-' % color, lw=2, label=description)

            ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

        if self.save_plot:
            self.output_file = os.path.join(os.getcwd(), os.path.basename(fname)) + '.png'
            fig.savefig(self.output_file, bbox_inches='tight')
        else:
            plt.show()

