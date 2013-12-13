#!/usr/bin/env python

# TODO: Use sane defaults for block size and file size, if not specified.
#		Handle header output for multiple files.

import os
import sys
import curses
import platform
import binwalk.module
import binwalk.common as common
from binwalk.compat import *

class HexDiff(object):

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

	NAME = "Binary Diffing"
	CLI = [
			binwalk.module.ModuleOption(short='W',
										long='hexdump',
										kwargs={'enabled' : True},
										description='Perform a hexdump / diff of a file or files'),
			binwalk.module.ModuleOption(short='G',
										long='green',
										kwargs={'show_green' : True, 'show_blue' : False, 'show_green' : False},
										description='Only show lines containing bytes that are the same among all files'),
			binwalk.module.ModuleOption(short='i',
										long='red',
										kwargs={'show_red' : True, 'show_blue' : False, 'show_green' : False},
										description='Only show lines containing bytes that are different among all files'),
			binwalk.module.ModuleOption(short='U',
										long='blue',
										kwargs={'show_blue' : True, 'show_red' : False, 'show_green' : False},
										description='Only show lines containing bytes that are different among some files'),
			binwalk.module.ModuleOption(short='w',
										long='terse',
										kwargs={'terse' : True},
										description='Diff all files, but only display a hex dump of the first file'),
	]
	
	KWARGS = [
			binwalk.module.ModuleKwarg(name='show_red', default=True),
			binwalk.module.ModuleKwarg(name='show_blue', default=True),
			binwalk.module.ModuleKwarg(name='show_green', default=True),
			binwalk.module.ModuleKwarg(name='terse', default=False),
	]

	def __init__(self, **kwargs):
		binwalk.module.process_kwargs(self, kwargs)

		self.block_hex = ""
		self.printed_alt_text = False

		if hasattr(sys.stderr, 'isatty') and sys.stderr.isatty() and platform.system() != 'Windows':
			curses.setupterm()
			self.colorize = self._colorize
		else:
			self.colorize = self._no_colorize

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
		printed = False

		if self._color_filter(self.block_hex):
			self.config.display.result(self.block_hex)
			self.printed_alt_text = False
			printed = True
		elif not self.printed_alt_text:
			self.config.display.result("%s\n" % alt_text)
			self.printed_alt_text = True
			printed = True

		self.block_hex = ""
		return printed

	def _build_block(self, c, highlight=None):
		if highlight == self.ALL_DIFF:
			self.block_hex += self.colorize(c, color="red")
		elif highlight == self.ALL_SAME:
			self.block_hex += self.colorize(c, color="green")
		elif highlight == self.SOME_DIFF:
			self.block_hex += self.colorize(c, color="blue")
		else:
			self.block_hex += c

	def run(self):
		i = 0
		total = 0
		fps = []
		data = {}
		delim = '/'

		offset = self.config.offset
		size = self.config.length
		block = self.config.block
		files = self.config.target_files

		self.config.display.format_strings("\n%s\n", "%s\n")

		# If negative offset, then we're going that far back from the end of the file
		if offset < 0:
			size = offset * -1

		# TODO: Display all file names in hexdump
		if self.terse:
			self.config.display.header(files[0])
		else:
			self.config.display.header(files[0])

		if common.BlockFile.READ_BLOCK_SIZE < block:
			read_block_size = block
		else:
			read_block_size = common.BlockFile.READ_BLOCK_SIZE

		for f in files:
			fp = common.BlockFile(f, 'r', length=size, offset=offset)
			fp.READ_BLOCK_SIZE = read_block_size
			fp.MAX_TRAILING_SIZE = 0
			fps.append(fp)

		# BlockFile handles calculation of negative offsets, if one was specified
		offset = fps[0].offset

		while total < size:
			i = 0
			files_finished = 0

			for fp in fps:
				(ddata, dlen) = fp.read_block()
				data[fp.name] = ddata
				if not ddata or dlen == 0:
					files_finished += 1
			
			if files_finished == len(fps):
				break
			
			while i < read_block_size and (total+i) < size:
				diff_same = {}
				alt_text = "*" + " " * 6

				self._build_block("%.08X  " % (total + i + offset))

				# For each byte in this block, is the byte the same in all files, the same in some files, or different in all files?
				for j in range(0, block):
					byte_list = []

					try:
						c = data[files[0]][j+i]
					except:
						c = None

					for f in files:
						try:
							c = data[f][j+i]
						except Exception as e:
							c = None

						if c not in byte_list:
							byte_list.append(c)

					if len(byte_list) == 1:
						diff_same[j] = self.ALL_SAME
					elif len(byte_list) == len(files):
						diff_same[j] = self.ALL_DIFF
					else:
						diff_same[j] = self.SOME_DIFF

				for index in range(0, len(files)):
					if self.terse and index > 0:
						break
			
					f = files[index]

					alt_text += " " * (3 + (3 * block) + 3 + block + 3)
					alt_text += delim

					for j in range(0, block):
						try:
							self._build_block("%.2X " % ord(data[f][j+i]), highlight=diff_same[j])
						except Exception as e:
							self._build_block("   ")

						if (j+1) == block:
							self._build_block(" |")
							for k in range(0, block):
								try:
									if data[f][k+i] in string.printable and data[f][k+i] not in string.whitespace:
										self._build_block(data[f][k+i], highlight=diff_same[k])
									else:
										self._build_block('.', highlight=diff_same[k])
								except:
									self._build_block(' ')

							if index == len(files)-1 or (self.terse and index == 0):
								self._build_block("|\n")
							else:
								self._build_block('|   %s   ' % delim)

				if self._print_block_hex(alt_text=alt_text[:-1].strip()):
					if delim == '\\':
						delim = '/'
					else:
						delim = '\\'

				i += block
			total += read_block_size
		
		for fp in fps:
			fp.close()

		self.config.display.footer()

		return True

