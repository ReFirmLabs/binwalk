import sys
import csv as pycsv
import datetime
import binwalk.core.common
from binwalk.core.compat import *

class Display(object):
    '''
    Class to handle display of output and writing to log files.
    This class is instantiated for all modules implicitly and should not need to be invoked directly by most modules.
    '''
    SCREEN_WIDTH = 0
    HEADER_WIDTH = 150
    DEFAULT_FORMAT = "%s\n"

    def __init__(self, quiet=False, verbose=False, log=None, csv=False, fit_to_screen=False, filter=None):
        self.quiet = quiet
        self.filter = filter
        self.verbose = verbose
        self.fit_to_screen = fit_to_screen
        self.fp = None
        self.csv = None
        self.num_columns = 0
        self.custom_verbose_format = ""
        self.custom_verbose_args = []

        self._configure_formatting()

        if log:
            self.fp = open(log, "w")
            if csv:
                self.csv = pycsv.writer(self.fp)

    def format_strings(self, header, result):
        self.result_format = result
        self.header_format = header
        
        if self.num_columns == 0:
            self.num_columns = len(header.split())

    def log(self, fmt, columns):
        if self.fp:
            if self.csv:
                self.csv.writerow(columns)
            else:
                self.fp.write(fmt % tuple(columns))

    def add_custom_header(self, fmt, args):
        self.custom_verbose_format = fmt
        self.custom_verbose_args = args

    def header(self, *args, **kwargs):
        file_name = None
        self.num_columns = len(args)

        if has_key(kwargs, 'file_name'):
            file_name = kwargs['file_name']

        if self.verbose and file_name:
            md5sum = binwalk.core.common.file_md5(file_name)
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if self.csv:
                self.log("", ["FILE", "MD5SUM", "TIMESTAMP"])
                self.log("", [file_name, md5sum, timestamp])

            self._fprint("%s", "\n", csv=False)
            self._fprint("Scan Time:     %s\n", [timestamp], csv=False, filter=False)
            self._fprint("Target File:   %s\n", [file_name], csv=False, filter=False)
            self._fprint("MD5 Checksum:  %s\n", [md5sum], csv=False, filter=False)
            if self.custom_verbose_format and self.custom_verbose_args:
                self._fprint(self.custom_verbose_format, self.custom_verbose_args, csv=False, filter=False)

        self._fprint("%s", "\n", csv=False, filter=False)
        self._fprint(self.header_format, args, filter=False)
        self._fprint("%s", ["-" * self.HEADER_WIDTH + "\n"], csv=False, filter=False)

    def result(self, *args):
        # Convert to list for item assignment
        args = list(args)

        # Replace multiple spaces with single spaces. This is to prevent accidentally putting
        # four spaces in the description string, which would break auto-formatting.
        for i in range(len(args)):
            if isinstance(args[i], str):
                while "  " in args[i]:
                    args[i] = args[i].replace("  " , " ")

        self._fprint(self.result_format, tuple(args))

    def footer(self):
        self._fprint("%s", "\n", csv=False, filter=False)

    def _fprint(self, fmt, columns, csv=True, stdout=True, filter=True):
        line = fmt % tuple(columns)
        
        if not filter or self.filter.valid_result(line):
            if not self.quiet and stdout:
                sys.stdout.write(self._format_line(line.strip()) + "\n")

            if self.fp and not (self.csv and not csv):
                self.log(fmt, columns)

    def _append_to_data_parts(self, data, start, end):
        '''
        Intelligently appends data to self.string_parts.
        For use by self._format.
        '''
        try:
            while data[start] == ' ':
                start += 1

            if start == end:
                end = len(data[start:])

            self.string_parts.append(data[start:end])
        except KeyboardInterrupt as e:
            raise e
        except Exception:
            try:
                self.string_parts.append(data[start:])
            except KeyboardInterrupt as e:
                raise e
            except Exception:
                pass
        
        return start

    def _format_line(self, line):
        '''
        Formats a line of text to fit in the terminal window.
        For Tim.
        '''
        offset = 0
        space_offset = 0
        self.string_parts = []
        delim = '\n'

        if self.fit_to_screen and len(line) > self.SCREEN_WIDTH:
            line_columns = line.split(None, self.num_columns-1)

            if line_columns:
                delim = '\n' + ' ' * line.rfind(line_columns[-1])

                while len(line[offset:]) > self.SCREEN_WIDTH:
                    space_offset = line[offset:offset+self.HEADER_WIDTH].rfind(' ')
                    if space_offset == -1 or space_offset == 0:
                        space_offset = self.SCREEN_WIDTH

                    self._append_to_data_parts(line, offset, offset+space_offset)

                    offset += space_offset

        self._append_to_data_parts(line, offset, offset+len(line[offset:]))

        return delim.join(self.string_parts)

    def _configure_formatting(self):
        '''
        Configures output formatting, and fitting output to the current terminal width.

        Returns None.
        '''
        self.format_strings(self.DEFAULT_FORMAT, self.DEFAULT_FORMAT)

        if self.fit_to_screen:
            try:
                import fcntl
                import struct
                import termios

                # Get the terminal window width
                hw = struct.unpack('hh', fcntl.ioctl(1, termios.TIOCGWINSZ, '1234'))
                self.SCREEN_WIDTH = self.HEADER_WIDTH = hw[1]
            except KeyboardInterrupt as e:
                raise e
            except Exception:
                pass

