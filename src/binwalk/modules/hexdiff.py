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
		'red'	: '31',
		'green'	: '32',
		'blue'	: '34',
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

	def _print_block_hex(self, alt_text="*"):
		if self._color_filter(self.block_hex):
			desc = self.block_hex
			self.printed_alt_text = False
		elif not self.printed_alt_text:
			desc = "%s" % alt_text
			self.printed_alt_text = True

		self.result(description=desc)
		self.block_hex = ""
		return True

	def _build_block(self, c, highlight=None):
		if highlight == self.ALL_DIFF:
			self.block_hex += self.colorize(c, color="red")
		elif highlight == self.ALL_SAME:
			self.block_hex += self.colorize(c, color="green")
		elif highlight == self.SOME_DIFF:
			self.block_hex += self.colorize(c, color="blue")
		else:
			self.block_hex += c

	def _build_header(self, files, block_size):
		header = "OFFSET" + (" " * 6) + files[0].name

		for i in range(1, len(files)):
			header += " " * ((block_size * 3) + 2 + block_size + 8 - len(files[i-1].name))
			header += files[i].name

		return header

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
		i = 0
		total = 0
		data = {}
		delim = '/'

		self.block_hex = ""
		self.printed_alt_text = False
		
		offset = self.config.offset
		size = self.config.length
		block = self.config.block

		self.header()

		if not block:
			block = self.DEFAULT_BLOCK_SIZE

		# If negative offset, then we're going that far back from the end of the file
		if offset < 0:
			size = offset * -1

		if common.BlockFile.READ_BLOCK_SIZE < block:
			read_block_size = block
		else:
			read_block_size = common.BlockFile.READ_BLOCK_SIZE

		# BlockFile handles calculation of negative offsets, if one was specified
		offset = self.config.target_files[0].offset
		size = self.config.target_files[0].length

		while total < size:
			i = 0
			files_finished = 0

			for fp in self.config.target_files:
				(ddata, dlen) = fp.read_block()
				data[fp.name] = ddata
				if not ddata or dlen == 0:
					files_finished += 1
			
			if files_finished == len(self.config.target_files):
				break
			
			while i < read_block_size and (total+i) < size:
				diff_same = {}
				alt_text = "*" + " " * 8

				self._build_block("%.08X    " % (total + i + offset))

				# For each byte in this block, is the byte the same in all files, the same in some files, or different in all files?
				for j in range(0, block):
					byte_list = []

					try:
						c = data[self.config.target_files[0].name][j+i]
					except:
						c = None

					for f in self.config.target_files:
						try:
							c = data[f.name][j+i]
						except Exception as e:
							c = None

						if c not in byte_list:
							byte_list.append(c)

					if len(byte_list) == 1:
						diff_same[j] = self.ALL_SAME
					elif len(byte_list) == len(self.config.target_files):
						diff_same[j] = self.ALL_DIFF
					else:
						diff_same[j] = self.SOME_DIFF

				for index in range(0, len(self.config.target_files)):
					if self.terse and index > 0:
						break
			
					f = self.config.target_files[index]

					alt_text += " " * (3 + (3 * block) + 3 + block + 3)
					alt_text += delim

					for j in range(0, block):
						try:
							self._build_block("%.2X " % ord(data[f.name][j+i]), highlight=diff_same[j])
						except KeyboardInterrupt as e:
							raise e
						except Exception as e:
							self._build_block("   ")

						if (j+1) == block:
							self._build_block(" |")
							for k in range(0, block):
								try:
									if data[f.name][k+i] in string.printable and data[f.name][k+i] not in string.whitespace:
										self._build_block(data[f.name][k+i], highlight=diff_same[k])
									else:
										self._build_block('.', highlight=diff_same[k])
								except:
									self._build_block(' ')

							if index == len(self.config.target_files)-1 or (self.terse and index == 0):
								self._build_block("|")
							else:
								self._build_block('|   %s   ' % delim)

				if self._print_block_hex(alt_text=alt_text[:-1].strip()):
					if delim == '\\':
						delim = '/'
					else:
						delim = '\\'

				i += block
			total += read_block_size

		self.footer()		
		return True

