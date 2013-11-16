#!/usr/bin/env python

import os
import sys
import string
import curses
import platform
import common

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

	def __init__(self, binwalk=None):
		self.block_hex = ""
		self.printed_alt_text = False

		if binwalk:
			self._pprint = binwalk.display._pprint
			self._show_header = binwalk.display.header
			self._footer = binwalk.display.footer
			self._display_result = binwalk.display.results
			self._grep = binwalk.filter.grep
		else:
			self._pprint = sys.stdout.write
			self._show_header = self._print
			self._footer = self._simple_footer
			self._display_result = self._print
			self._grep = None

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

	def _print_block_hex(self, alt_text="*"):
		printed = False

		if self._grep is None or self._grep(self.block_hex):
			self._pprint(self.block_hex)
			self.printed_alt_text = False
			printed = True
		elif not self.printed_alt_text:
			self._pprint("%s\n" % alt_text)
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

	def _simple_footer(self):
		print ""

	def _header(self, files, block):
		header = "OFFSET    "
		for i in range(0, len(files)):
			f = files[i]
			header += "%s" % os.path.basename(f)
			if i != len(files)-1:
				header += " " * ((block*4) + 10 - len(os.path.basename(f)))
		self._show_header(header=header)

	def display(self, files, offset=0, size=DEFAULT_DIFF_SIZE, block=DEFAULT_BLOCK_SIZE, show_first_only=False):
		i = 0
		total = 0
		fps = []
		data = {}
		delim = '/'

		if show_first_only:
			self._header([files[0]], block)
		else:
			self._header(files, block)

		if common.BlockFile.READ_BLOCK_SIZE < block:
			read_block_size = block
		else:
			read_block_size = common.BlockFile.READ_BLOCK_SIZE

		for f in files:
			fp = common.BlockFile(f, 'rb', length=size, offset=offset)
			fp.READ_BLOCK_SIZE = read_block_size
			fp.MAX_TRAILING_SIZE = 0
			fps.append(fp)

		# BlockFile handles calculation of negative offsets, if one was specified
		offset = fps[0].offset

		while total < size:
			i = 0
			for fp in fps:
				(ddata, dlen) = fp.read_block()
				data[fp.name] = ddata
			
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
						except Exception, e:
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
					if show_first_only and index > 0:
						break
			
					f = files[index]

					alt_text += " " * (3 + (3 * block) + 3 + block + 3)
					alt_text += delim

					for j in range(0, block):
						try:
							#print "%s[%d]" % (f, j+i)
							self._build_block("%.2X " % ord(data[f][j+i]), highlight=diff_same[j])
						except Exception, e:
							#print str(e)
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

							if index == len(files)-1 or (show_first_only and index == 0):
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

		self._footer()

if __name__ == "__main__":
	HexDiff().display(sys.argv[1:])

