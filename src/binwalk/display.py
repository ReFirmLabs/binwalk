import sys
import csv as pycsv
import binwalk.common

class Display(object):

	BUFFER_WIDTH = 32
	HEADER_WIDTH = 115
	MAX_LINE_LEN = 0
	DEFAULT_FORMAT = "%s\n"

	def __init__(self, quiet=False, verbose=0, log=None, csv=False, fit_to_screen=False):
		self.quiet = quiet
		self.verbose = verbose
		self.fit_to_screen = fit_to_screen
		self.fp = None
		self.csv = None

		self._configure_formatting()

		if log:
			self.fp = binwalk.common.BlockFile(log, mode="w")
			if self.csv:
				self.csv = pycsv.writer(self.fp)

	def format_strings(self, header, result):
		self.result_format = result
		self.header_format = header

	def log(self, fmt, columns):
		if self.fp:
			if self.csv:
				self.csv.writerow(columns)
			else:
				self.fp.write(fmt % tuple(columns))

	def header(self, *args):
		self._fprint(self.header_format, args)
		self._fprint("%s", ["-" * self.HEADER_WIDTH + "\n"], csv=False)

	def result(self, *args):
		self._fprint(self.result_format, args)

	def footer(self):
		self._fprint("%s", "\n", csv=False)

	def _fprint(self, fmt, columns, csv=True):
		if not self.quiet:
			sys.stdout.write(fmt % tuple(columns))

		if not (self.csv and not csv):
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
		except:
			try:
				self.string_parts.append(data[start:])
			except:
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
		delim = '\n' + ' ' * self.BUFFER_WIDTH

		if self.fit_to_screen:
			while len(line[offset:]) > self.MAX_LINE_LEN:
				space_offset = line[offset:offset+self.MAX_LINE_LEN].rfind(' ')
				if space_offset == -1 or space_offset == 0:
					space_offset = self.MAX_LINE_LEN

				self._append_to_data_parts(line, offset, offset+space_offset)

				offset += space_offset

		self._append_to_data_parts(line, offset, offset+len(data[offset:]))

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
				self.HEADER_WIDTH = hw[1]
			except Exception as e:
				pass

			self.MAX_LINE_LEN = self.HEADER_WIDTH - self.BUFFER_WIDTH

