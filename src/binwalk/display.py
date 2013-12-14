import sys
import csv as pycsv

class Display(object):

	SCREEN_WIDTH = 0
	HEADER_WIDTH = 150
	DEFAULT_FORMAT = "%s\n"

	def __init__(self, quiet=False, verbose=0, log=None, csv=False, fit_to_screen=False):
		self.quiet = quiet
		self.verbose = verbose
		self.fit_to_screen = fit_to_screen
		self.fp = None
		self.csv = None
		self.num_columns = 0

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

	def header(self, *args):
		self.num_columns = len(args)
		self._fprint("%s", "\n", csv=False)
		self._fprint(self.header_format, args)
		self._fprint("%s", ["-" * self.HEADER_WIDTH + "\n"], csv=False)

	def result(self, *args):
		self._fprint(self.result_format, args)

	def footer(self):
		self._fprint("%s", "\n", csv=False)

	def _fprint(self, fmt, columns, csv=True):
		if not self.quiet:
			line = fmt % tuple(columns)
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
			except Exception as e:
				pass

