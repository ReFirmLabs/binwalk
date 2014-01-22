import os
import sys
import curses
import platform
import binwalk.core.common as common
from binwalk.core.compat import *
from binwalk.core.module import Module, Option, Kwarg

# TODO: This code is an effing mess.
class HexDiff(Module):

    ALL_SAME = 0
    ALL_DIFF = 1
    SOME_DIFF = 2

    DEFAULT_DIFF_SIZE = 0x100
    DEFAULT_BLOCK_SIZE = 16

    COLORS = {
        'red'    : '31',
        'green'    : '32',
        'blue'    : '34',
    }

    TITLE = "Binary Diffing"

    CLI = [
            Option(short='W',
                   long='hexdump',
                   kwargs={'enabled' : True},
                   description='Perform a hexdump / diff of a file or files'),
            Option(short='G',
                   long='green',
                   kwargs={'show_green' : True, 'show_blue' : False, 'show_red' : False},
                   description='Only show lines containing bytes that are the same among all files'),
            Option(short='i',
                   long='red',
                   kwargs={'show_red' : True, 'show_blue' : False, 'show_green' : False},
                   description='Only show lines containing bytes that are different among all files'),
            Option(short='U',
                   long='blue',
                   kwargs={'show_blue' : True, 'show_red' : False, 'show_green' : False},
                   description='Only show lines containing bytes that are different among some files'),
            Option(short='w',
                   long='terse',
                   kwargs={'terse' : True},
                   description='Diff all files, but only display a hex dump of the first file'),
    ]
    
    KWARGS = [
            Kwarg(name='show_red', default=True),
            Kwarg(name='show_blue', default=True),
            Kwarg(name='show_green', default=True),
            Kwarg(name='terse', default=False),
            Kwarg(name='enabled', default=False),
    ]

    HEADER_FORMAT = "\n%s\n"
    RESULT_FORMAT = "%s\n"
    RESULT = ['description']
    
    def _no_colorize(self, c, color="red", bold=True):
        return c

    def _colorize(self, c, color="red", bold=True):
        attr = []

        attr.append(self.COLORS[color])
        if bold:
            attr.append('1')

        return "\x1b[%sm%s\x1b[0m" % (';'.join(attr), c)

    def _color_filter(self, data):
        red = '\x1b[' + self.COLORS['red'] + ';'
        green = '\x1b[' + self.COLORS['green'] + ';'
        blue = '\x1b[' + self.COLORS['blue'] + ';'

        if self.show_blue and blue in data:
            return True
        if self.show_green and green in data:
            return True
        if self.show_red and red in data:
            return True
        return False

    def init(self):
        block = self.config.block
        if not block:
            block = self.DEFAULT_BLOCK_SIZE

        if self.terse:
            header_files = self.config.target_files[:1]
        else:
            header_files = self.config.target_files

        self.HEADER = self._build_header(header_files, block)

        if hasattr(sys.stderr, 'isatty') and sys.stderr.isatty() and platform.system() != 'Windows':
            curses.setupterm()
            self.colorize = self._colorize
        else:
            self.colorize = self._no_colorize

    def run(self):
        
        return True

