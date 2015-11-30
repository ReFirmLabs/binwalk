# Code to handle displaying and logging of results.
# Anything in binwalk that prints results to screen should use this class.

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
    HEADER_WIDTH = 80
    DEFAULT_FORMAT = "%s\n"

    def __init__(self, quiet=False, verbose=False, log=None, csv=False, fit_to_screen=False):
        self.quiet = quiet
        self.verbose = verbose
        self.fit_to_screen = fit_to_screen
        self.fp = None
        self.csv = None
        self.num_columns = 0
        self.custom_verbose_format = ""
        self.custom_verbose_args = []

        self._configure_formatting()

        if log:
            self.fp = open(log, "a")
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

            self.fp.flush()

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
                while "    " in args[i]:
                    args[i] = args[i].replace("  " , " ")

        self._fprint(self.result_format, tuple(args))

    def footer(self):
        self._fprint("%s", "\n", csv=False, filter=False)

    def _fprint(self, fmt, columns, csv=True, stdout=True, filter=True):
        line = fmt % tuple(columns)

        if not self.quiet and stdout:
            try:
                sys.stdout.write(self._format_line(line.strip()) + "\n")
                sys.stdout.flush()
            except IOError as e:
                pass

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
        delim = '\n'
        offset = 0
        self.string_parts = []

        # Split the line into an array of columns, e.g., ['0', '0x00000000', 'Some description here']
        line_columns = line.split(None, self.num_columns-1)
        if line_columns:
            # Find where the start of the last column (description) starts in the line of text.
            # All line wraps need to be aligned to this offset.
            offset = line.rfind(line_columns[-1])
            # The delimiter will be a newline followed by spaces padding out the line wrap to the alignment offset.
            delim += ' ' * offset

        if line_columns and self.fit_to_screen and len(line) > self.SCREEN_WIDTH:
            # Calculate the maximum length that each wrapped line can be
            max_line_wrap_length = self.SCREEN_WIDTH - offset
            # Append all but the last column to formatted_line
            formatted_line = line[:offset]

            # Loop to split up line into multiple max_line_wrap_length pieces
            while len(line[offset:]) > max_line_wrap_length:
                # Find the nearest space to wrap the line at (so we don't split a word across two lines)
                split_offset = line[offset:offset+max_line_wrap_length].rfind(' ')
                # If there were no good places to split the line, just truncate it at max_line_wrap_length
                if split_offset < 1:
                    split_offset = max_line_wrap_length

                self._append_to_data_parts(line, offset, offset+split_offset)
                offset += split_offset

            # Add any remaining data (guarunteed to be max_line_wrap_length long or shorter) to self.string_parts
            self._append_to_data_parts(line, offset, offset+len(line[offset:]))

            # Append self.string_parts to formatted_line; each part seperated by delim
            formatted_line += delim.join(self.string_parts)
        else:
            formatted_line = line

        return formatted_line

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

