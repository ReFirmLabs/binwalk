import os
import sys
import argparse
import binwalk.common
import binwalk.module
import binwalk.config
import binwalk.display
from binwalk.config import *
from binwalk.compat import *

class Configuration(binwalk.module.Module):

	TITLE = "General"

	DEPENDS = {}
		
	CLI = [
		binwalk.module.ModuleOption(long='length',
									short='l',
									type=int,
									kwargs={'length' : 0},
									description='Number of bytes to scan'),
		binwalk.module.ModuleOption(long='offset',
									short='o',
									type=int,
									kwargs={'offset' : 0},
									description='Start scan at this file offset'),
		binwalk.module.ModuleOption(long='block',
									short='K',
									type=int,
									kwargs={'block' : 0},
									description='Set file block size'),
		binwalk.module.ModuleOption(long='swap',
									short='g',
									type=int,
									kwargs={'swap_size' : 0},
									description='Reverse every n bytes before scanning'),
		binwalk.module.ModuleOption(long='log',
									short='f',
									type=argparse.FileType,
									kwargs={'log_file' : None},
									description='Log results to file'),
		binwalk.module.ModuleOption(long='csv',
									short='c',
									kwargs={'csv' : True},
									description='Log results to file in CSV format'),
		binwalk.module.ModuleOption(long='term',
									short='t',
									kwargs={'format_to_terminal' : True},
									description='Format output to fit the terminal window'),
		binwalk.module.ModuleOption(long='quiet',
									short='q',
									kwargs={'quiet' : True},
									description='Supress output to stdout'),
		binwalk.module.ModuleOption(long='verbose',
									short='v',
									type=list,
									kwargs={'verbose' : True},
									description='Enable verbose output (specify twice for more verbosity)'),
		binwalk.module.ModuleOption(short='h',
									long='help',
									kwargs={'show_help' : True},
									description='Show help output'),
		binwalk.module.ModuleOption(long=None,
									short=None,
									type=binwalk.common.BlockFile,
									kwargs={'files' : []}),
	]

	KWARGS = [
		binwalk.module.ModuleKwarg(name='length', default=0),
		binwalk.module.ModuleKwarg(name='offset', default=0),
		binwalk.module.ModuleKwarg(name='block', default=0),
		binwalk.module.ModuleKwarg(name='swap_size', default=0),
		binwalk.module.ModuleKwarg(name='log_file', default=None),
		binwalk.module.ModuleKwarg(name='csv', default=False),
		binwalk.module.ModuleKwarg(name='format_to_terminal', default=False),
		binwalk.module.ModuleKwarg(name='quiet', default=False),
		binwalk.module.ModuleKwarg(name='verbose', default=[]),
		binwalk.module.ModuleKwarg(name='files', default=[]),
		binwalk.module.ModuleKwarg(name='show_help', default=False),
	]

	def load(self):
		self.target_files = []
		
		self._set_verbosity()
		self._open_target_files()

		self.settings = binwalk.config.Config()
		self.display = binwalk.display.Display(log=self.log_file,
											   csv=self.csv,
											   quiet=self.quiet,
											   verbose=self.verbose,
											   fit_to_screen=self.format_to_terminal)
		
		if self.show_help:
			binwalk.module.show_help()
			sys.exit(0)

	def __del__(self):
		self._cleanup()

	def __exit__(self, a, b, c):
		self._cleanup()

	def __enter__(self):
		return self

	def _cleanup(self):
		for fp in self.target_files:
			fp.close()

	def _set_verbosity(self):
		'''
		Sets the appropriate verbosity.
		Must be called after self._test_target_files so that self.target_files is properly set.
		'''
		self.verbose = len(self.verbose)

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
					fp = binwalk.common.BlockFile(tfile, length=self.length, offset=self.offset, swap=self.swap_size)
					self.target_files.append(fp)
				except KeyboardInterrupt as e:
					raise e
				except Exception as e:
					self.error(description="Cannot open file : %s" % str(e))
		
		# If no files could be opened, quit permaturely
		if len(self.target_files) == 0:
			raise Exception("Failed to open any files for scanning")

