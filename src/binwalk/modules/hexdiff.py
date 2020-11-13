import sys
import string
import binwalk.core.common as common
from binwalk.core.compat import *
from binwalk.core.module import Module, Option, Kwarg


class HexDiff(Module):

    COLORS = {
        'red': '31',
        'green': '32',
        'blue': '34',
    }

    SEPERATORS = ['\\', '/']
    DEFAULT_BLOCK_SIZE = 16

    SKIPPED_LINE = "*"
    SAME_DIFFERENCE = "~"
    CUSTOM_DISPLAY_FORMAT = "0x%.8X    %s"

    TITLE = "Binary Diffing"

    CLI = [
        Option(short='W',
               long='hexdump',
               kwargs={'enabled': True},
               description='Perform a hexdump / diff of a file or files'),
        Option(short='G',
               long='green',
               kwargs={'show_green': True},
               description='Only show lines containing bytes that are the same among all files'),
        Option(short='i',
               long='red',
               kwargs={'show_red': True},
               description='Only show lines containing bytes that are different among all files'),
        Option(short='U',
               long='blue',
               kwargs={'show_blue': True},
               description='Only show lines containing bytes that are different among some files'),
        Option(short='u',
               long='similar',
               kwargs={'show_same': True},
               description='Only display lines that are the same between all files'),
        Option(short='w',
               long='terse',
               kwargs={'terse': True},
               description='Diff all files, but only display a hex dump of the first file'),
    ]

    KWARGS = [
        Kwarg(name='show_red', default=False),
        Kwarg(name='show_blue', default=False),
        Kwarg(name='show_green', default=False),
        Kwarg(name='terse', default=False),
        Kwarg(name='show_same', default=False),
        Kwarg(name='enabled', default=False),
    ]

    RESULT_FORMAT = "%s\n"
    RESULT = ['display']

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
        elif self.show_green and green in data:
            return True
        elif self.show_red and red in data:
            return True

        return False

    def hexascii(self, target_data, byte, offset):
        color = "green"

        for (fp_i, data_i) in iterator(target_data):
            diff_count = 0

            for (fp_j, data_j) in iterator(target_data):
                if fp_i == fp_j:
                    continue

                try:
                    if data_i[offset] != data_j[offset]:
                        diff_count += 1
                except IndexError as e:
                    diff_count += 1

            if diff_count == len(target_data) - 1:
                color = "red"
            elif diff_count > 0:
                color = "blue"
                break

        hexbyte = self.colorize("%.2X" % ord(byte), color)

        if byte not in string.printable or byte in string.whitespace:
            byte = "."

        asciibyte = self.colorize(byte, color)

        return (hexbyte, asciibyte)

    def diff_files(self, target_files):
        last_raw_line = None
        last_line = None
        loop_count = 0
        sep_count = 0

        # Figure out the maximum diff size (largest file size)
        self.status.total = 0
        for i in range(0, len(target_files)):
            if target_files[i].size > self.status.total:
                self.status.total = target_files[i].size
                self.status.fp = target_files[i]

        while True:
            line = ""
            current_raw_line = ""
            done_files = 0
            block_data = {}
            seperator = self.SEPERATORS[sep_count % 2]

            for fp in target_files:
                block_data[fp] = fp.read(self.block)
                if not block_data[fp]:
                    done_files += 1

            # No more data from any of the target files? Done.
            if done_files == len(target_files):
                break

            for fp in target_files:
                hexline = ""
                asciiline = ""

                for i in range(0, self.block):
                    if i >= len(block_data[fp]):
                        hexbyte = "XX"
                        asciibyte = "."
                    else:
                        (hexbyte, asciibyte) = self.hexascii(block_data, block_data[fp][i], i)

                    hexline += "%s " % hexbyte
                    asciiline += "%s" % asciibyte

                line += "%s |%s|" % (hexline, asciiline)

                if self.terse:
                    break

                if fp != target_files[-1]:
                    # Need to keep a copy of the line data without the seperator, since the sep changes
                    # every other line. This allows us to compare one raw line to a previous raw line to
                    # see if they are the same.
                    current_raw_line += line
                    line += " %s " % seperator

            offset = fp.offset + (self.block * loop_count)

            if current_raw_line == last_raw_line and self.show_same == True:
                display = line = self.SAME_DIFFERENCE
            elif not self._color_filter(line):
                display = line = self.SKIPPED_LINE
            else:
                display = self.CUSTOM_DISPLAY_FORMAT % (offset, line)
                sep_count += 1

            if (line not in [self.SKIPPED_LINE, self.SAME_DIFFERENCE] or
                    (last_line != line and
                        (last_line not in [self.SKIPPED_LINE, self.SAME_DIFFERENCE] or
                         line not in [self.SKIPPED_LINE, self.SAME_DIFFERENCE]))):
                self.result(offset=offset, description=line, display=display)

            last_line = line
            last_raw_line = current_raw_line
            loop_count += 1
            self.status.completed += self.block

    def init(self):
        # To mimic expected behavior, if all options are False, we show
        # everything
        if not any([self.show_red, self.show_green, self.show_blue]):
            self.show_red = self.show_green = self.show_blue = True

        # Always disable terminal formatting, as it won't work properly with
        # colorized output
        self.config.display.fit_to_screen = False

        # Set the block size (aka, hexdump line size)
        self.block = self.config.block
        if not self.block:
            self.block = self.DEFAULT_BLOCK_SIZE

        # Build a list of files to hexdiff
        self.hex_target_files = []
        while True:
            f = self.next_file(close_previous=False)
            if not f:
                break
            else:
                self.hex_target_files.append(f)

        # Build the header format string
        header_width = (self.block * 4) + 2
        if self.terse:
            file_count = 1
        else:
            file_count = len(self.hex_target_files)
        self.HEADER_FORMAT = "OFFSET      " + \
            (("%%-%ds   " % header_width) * file_count) + "\n"

        # Build the header argument list
        self.HEADER = [fp.name for fp in self.hex_target_files]
        if self.terse and len(self.HEADER) > 1:
            self.HEADER = self.HEADER[0]

        # Set up the tty for colorization, if it is supported
        if hasattr(sys.stderr, 'isatty') and sys.stderr.isatty() and not common.MSWindows():
            import curses
            curses.setupterm()
            self.colorize = self._colorize
        else:
            self.colorize = self._no_colorize

    def run(self):
        if self.hex_target_files:
            self.header()
            self.diff_files(self.hex_target_files)
            self.footer()
