import sys
import hashlib
import csv as pycsv
from datetime import datetime
from binwalk.compat import *

class PrettyPrint:
	'''
	Class for printing binwalk results to screen/log files.
	
	An instance of PrettyPrint is available via the Binwalk.display object.
	The PrettyPrint.results() method is of particular interest, as it is suitable for use as a Binwalk.scan() callback function,
	and can be used to print Binwalk.scan() results to stdout, a log file, or both.

	Useful class objects:
	
		self.fp               - The log file's file object.
		self.quiet            - If set to True, all output to stdout is supressed.
		self.verbose          - If set to True, verbose output is enabled.
		self.csv              - If set to True, data will be saved to the log file in CSV format.
		self.format_to_screen - If set to True, output data will be formatted to fit into the current screen width.

	Example usage:

		import binwalk

		bw = binwalk.Binwalk()

		bw.display.header()
		bw.single_scan('firmware.bin', callback=bw.display.results)
		bw.display.footer()
	'''

	HEADER_WIDTH = 115
	BUFFER_WIDTH = 32
	MAX_LINE_LEN = 0
	DEFAULT_DESCRIPTION_HEADER = "DESCRIPTION"

	def __init__(self, binwalk, log=None, csv=False, quiet=False, verbose=0, format_to_screen=False):
		'''
		Class constructor.
		
		@binwalk          - An instance of the Binwalk class.
		@log              - Output log file.
		@csv              - If True, save data to log file in CSV format.
		@quiet            - If True, results will not be displayed to screen.
		@verbose          - If set to True, target file information will be displayed when file_info() is called.
		@format_to_screen - If set to True, format the output data to fit into the current screen width.

		Returns None.
		'''
		self.binwalk = binwalk
		self.fp = None
		self.log = log
		self.csv = None
		self.log_csv = csv
		self.quiet = quiet
		self.verbose = verbose
		self.format_to_screen = format_to_screen

		if self.format_to_screen:
			self.enable_formatting(True)

		if self.log is not None:
			self.fp = open(log, "w")
			
			if self.log_csv:
				self.enable_csv()

	def __del__(self):
		'''
		Class deconstructor.
		'''
		self.cleanup()

	def __exit__(self, t, v, traceback):
		self.cleanup()

	def cleanup(self):
		'''
		Clean up any open file descriptors.
		'''
		try:
			self.fp.close()
		except:
			pass

		self.fp = None

	def _log(self, data, raw=False):
		'''
		Log data to the log file.
		'''
		if self.fp is not None:
			
			if self.log_csv and self.csv and not raw:

				data = data.replace('\n', ' ')
				while '  ' in data:
					data = data.replace('  ', ' ')

				data_parts = data.split(None, 2)

				if len(data_parts) == 3:
					for i in range(0, len(data_parts)):
						data_parts[i] = data_parts[i].strip()

					self.csv.writerow(data_parts)
			else:
				self.fp.write(data)

	def _pprint(self, data, nolog=False, noprint=False):
		'''
		Print data to stdout and the log file.
		'''
		if not self.quiet and not noprint:
			sys.stdout.write(data)
		if not nolog:
			self._log(data)

	def _file_md5(self, file_name):
		'''
		Generate an MD5 hash of the specified file.
		'''
		md5 = hashlib.md5()
                
		with open(file_name, 'rb') as f:
			for chunk in iter(lambda: f.read(128*md5.block_size), b''):
				md5.update(chunk)

		return md5.hexdigest()

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

	def _format(self, data):
		'''
		Formats a line of text to fit in the terminal window.
		For Tim.
		'''
		offset = 0
		space_offset = 0
		self.string_parts = []
		delim = '\n' + ' ' * self.BUFFER_WIDTH

		if self.format_to_screen:
			while len(data[offset:]) > self.MAX_LINE_LEN:
				space_offset = data[offset:offset+self.MAX_LINE_LEN].rfind(' ')
				if space_offset == -1 or space_offset == 0:
					space_offset = self.MAX_LINE_LEN
	
				self._append_to_data_parts(data, offset, offset+space_offset)

				offset += space_offset

		self._append_to_data_parts(data, offset, offset+len(data[offset:]))

		return delim.join(self.string_parts)

	def enable_csv(self):
		'''
		Enables CSV formatting to log file.
		'''
		self.log_csv = True
		self.csv = pycsv.writer(self.fp)
		
	def enable_formatting(self, tf):
		'''
		Enables output formatting, which fits output to the current terminal width.

		@tf - If True, enable formatting. If False, disable formatting.

		Returns None.
		'''
		self.format_to_screen = tf

		if self.format_to_screen:
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
	
	def file_info(self, file_name):
		'''
		Prints detailed info about the specified file, including file name, scan time and the file's MD5 sum.
		Called internally by self.header if self.verbose is not 0.

		@file_name - The path to the target file.
		@binwalk   - Binwalk class instance.

		Returns None.
		'''
		nolog = False
		md5sum = self._file_md5(file_name)
		timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

		if self.csv:
			nolog = True
			self.csv.writerow(["FILE", "MD5SUM", "TIMESTAMP"])
			self.csv.writerow([file_name, md5sum, timestamp])

		self._pprint("\n")
		self._pprint("Scan Time:     %s\n" % timestamp, nolog=nolog)
		self._pprint("Signatures:    %d\n" % self.binwalk.parser.signature_count, nolog=nolog)
		self._pprint("Target File:   %s\n" % file_name, nolog=nolog)
		self._pprint("MD5 Checksum:  %s\n" % md5sum, nolog=nolog)

	def header(self, file_name=None, header=None, description=DEFAULT_DESCRIPTION_HEADER):
		'''
		Prints the binwalk header, typically used just before starting a scan.

		@file_name   - If specified, and if self.verbose > 0, then detailed file info will be included in the header.
		@header      - If specified, this is a custom header to display at the top of the output.
		@description - The description header text to display (default: "DESCRIPTION")

		Returns None.
		'''
		nolog = False

		if self.verbose and file_name is not None:
			self.file_info(file_name)

		if self.log_csv:
			nolog = True

		self._pprint("\n")

		if not header:
			self._pprint("DECIMAL   \tHEX       \t%s\n" % description, nolog=nolog)
		else:
			self._pprint(header + "\n", nolog=nolog)
		
		self._pprint("-" * self.HEADER_WIDTH + "\n", nolog=nolog)

	def footer(self, bwalk=None, file_name=None):
		'''
		Prints the binwalk footer, typically used just after completing a scan.

		Returns None.
		'''
		self._pprint("\n")

	def results(self, offset, results, formatted=False):
		'''
		Prints the results of a scan. Suitable for use as a callback function for Binwalk.scan().

		@offset    - The offset at which the results were found.
		@results   - A list of libmagic result strings.
		@formatted - Set to True if the result description has already been formatted properly.

		Returns None.
		'''
		offset_printed = False

		for info in results:
			# Check for any grep filters before printing
			if self.binwalk.filter.grep(info['description']):
				if not formatted:
				# Only display the offset once per list of results
					if not offset_printed:
						self._pprint("%-10d\t0x%-8X\t%s\n" % (offset, offset, self._format(info['description'])))
						offset_printed = True
					else:
						self._pprint("%s\t  %s\t%s\n" % (' '*10, ' '*8, self._format(info['description'])))
				else:
					self._pprint(info['description'])

	def easy_results(self, offset, description):
		'''
		Simpler wrapper around prettyprint.results.

		@offset      - The offset at which the result was found.
		@description - Description string to display.

		Returns None.
		'''
		results = {
			'offset' 	: offset,
			'description' 	: description,
		}

		return self.results(offset, [results])

