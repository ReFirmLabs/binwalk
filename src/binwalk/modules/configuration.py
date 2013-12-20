import os
import sys
import argparse
import binwalk.core.common
import binwalk.core.config
import binwalk.core.display
from binwalk.core.config import *
from binwalk.core.compat import *
from binwalk.core.module import Module, Option, Kwarg, show_help

class Configuration(Module):

	TITLE = "General"

	DEPENDS = {}
		
	CLI = [
		Option(long='length',
			   short='l',
			   type=int,
			   kwargs={'length' : 0},
			   description='Number of bytes to scan'),
		Option(long='offset',
			   short='o',
			   type=int,
			   kwargs={'offset' : 0},
			   description='Start scan at this file offset'),
		Option(long='block',
			   short='K',
			   type=int,
			   kwargs={'block' : 0},
			   description='Set file block size'),
		Option(long='swap',
			   short='g',
			   type=int,
			   kwargs={'swap_size' : 0},
			   description='Reverse every n bytes before scanning'),
		Option(long='log',
			   short='f',
			   type=argparse.FileType,
			   kwargs={'log_file' : None},
			   description='Log results to file'),
		Option(long='csv',
			   short='c',
			   kwargs={'csv' : True},
			   description='Log results to file in CSV format'),
		Option(long='term',
			   short='t',
			   kwargs={'format_to_terminal' : True},
			   description='Format output to fit the terminal window'),
		Option(long='quiet',
			   short='q',
			   kwargs={'quiet' : True},
			   description='Supress output to stdout'),
		Option(long='verbose',
			   short='v',
			   kwargs={'verbose' : 1},
			   description='Enable verbose output'),
		Option(short='h',
			   long='help',
			   kwargs={'show_help' : True},
			   description='Show help output'),
		Option(long=None,
			   short=None,
			   type=binwalk.core.common.BlockFile,
			   kwargs={'files' : []}),
	]

	KWARGS = [
		Kwarg(name='length', default=0),
		Kwarg(name='offset', default=0),
		Kwarg(name='block', default=0),
		Kwarg(name='swap_size', default=0),
		Kwarg(name='log_file', default=None),
		Kwarg(name='csv', default=False),
		Kwarg(name='format_to_terminal', default=False),
		Kwarg(name='quiet', default=False),
		Kwarg(name='verbose', default=0),
		Kwarg(name='files', default=[]),
		Kwarg(name='show_help', default=False),
	]

	def load(self):
		self.target_files = []
		
		self._open_target_files()
		self._set_verbosity()

		self.settings = binwalk.core.config.Config()
		self.display = binwalk.core.display.Display(log=self.log_file,
													csv=self.csv,
													quiet=self.quiet,
													verbose=self.verbose,
													fit_to_screen=self.format_to_terminal)
		
		if self.show_help:
			show_help()
			sys.exit(0)

	def __del__(self):
		self._cleanup()

	def __exit__(self, a, b, c):
		self._cleanup()

	def __enter__(self):
		return self

	def _cleanup(self):
		if hasattr(self, 'target_files'):
			for fp in self.target_files:
				fp.close()

	def _set_verbosity(self):
		'''
		Sets the appropriate verbosity.
		Must be called after self._test_target_files so that self.target_files is properly set.
		'''
		# If more than one target file was specified, enable verbose mode; else, there is
		# nothing in some outputs to indicate which scan corresponds to which file. 
		if len(self.target_files) > 1 and self.verbose == 0:
			self.verbose = 1

	def _open_target_files(self):
		'''
		Checks if the target files can be opened.
		Any files that cannot be opened are removed from the self.target_files list.
		'''
		# Validate the target files listed in target_files
		for tfile in self.files:
			# Ignore directories.
			if not os.path.isdir(tfile):
				# Make sure we can open the target files
				try:
					fp = binwalk.core.common.BlockFile(tfile, length=self.length, offset=self.offset, swap=self.swap_size)
					self.target_files.append(fp)
				except KeyboardInterrupt as e:
					raise e
				except Exception as e:
					self.error(description="Cannot open file : %s" % str(e))
		
		# If no files could be opened, quit permaturely
		if len(self.target_files) == 0:
			raise Exception("Failed to open any files for scanning")

