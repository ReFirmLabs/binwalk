import os
import sys
import binwalk.common
import binwalk.module
import binwalk.display

class Configuration(object):

	CLI = [
		binwalk.module.ModuleOption(long='length',
									short='l',
									nargs=1,
									type=int,
									kwargs={'length' : 0},
									description='Number of bytes to scan'),
		binwalk.module.ModuleOption(long='offset',
									short='o',
									nargs=1,
									type=int,
									kwargs={'offset' : 0},
									description='Start scan at this file offset'),
		binwalk.module.ModuleOption(long='grep',
									short='g',
									nargs=1,
									kwargs={'grep' : []},
									type=list,
									description='Grep results for the specified text'),
		binwalk.module.ModuleOption(long='log',
									short='f',
									nargs=1,
									kwargs={'log_file' : None},
									description='Log results to file'),
		binwalk.module.ModuleOption(long='csv',
									short='c',
									kwargs={'csv' : True},
									description='Log results to file in CSV format'),
		binwalk.module.ModuleOption(long='skip-unopened',
									short='O',
									kwargs={'skip_unopened' : True},
									description='Ignore file open errors and process only the files that can be opened'),
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
		binwalk.module.ModuleOption(long=None,
									short=None,
									type=binwalk.common.BlockFile,
									kwargs={'target_files' : []}),
	]

	KWARGS = [
		binwalk.module.ModuleKwarg(name='length', default=None),
		binwalk.module.ModuleKwarg(name='offset', default=None),
		binwalk.module.ModuleKwarg(name='log_file', default=None),
		binwalk.module.ModuleKwarg(name='csv', default=False),
		binwalk.module.ModuleKwarg(name='format_to_terminal', default=False),
		binwalk.module.ModuleKwarg(name='grep', default=[]),
		binwalk.module.ModuleKwarg(name='quiet', default=False),
		binwalk.module.ModuleKwarg(name='verbose', default=[]),
		binwalk.module.ModuleKwarg(name='debug_verbose', default=False),
		binwalk.module.ModuleKwarg(name='skip_unopened', default=False),
		binwalk.module.ModuleKwarg(name='target_files', default=[]),
	]

	def __init__(self, **kwargs):
		binwalk.module.process_kwargs(self, kwargs)

		self._test_target_files()
		self._set_verbosity()

		self.display = binwalk.display.Display(log=self.log_file,
											   csv=self.csv,
											   quiet=self.quiet,
											   verbose=self.verbose,
											   fit_to_screen=self.format_to_terminal)

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

	def _test_target_files(self):
		'''
		Checks if the target files can be opened.
		Any files that cannot be opened are removed from the self.target_files list.
		'''
		failed_open_count = 0

		# Validate the target files listed in target_files
		for tfile in self.target_files:
			# Ignore directories.
			if not os.path.isdir(tfile):
				# Make sure we can open the target files
				try:
					fd = open(tfile, "rb")
					fd.close()
				except Exception as e:
					sys.stderr.write("Cannot open file : %s\n" % str(e))
					self.target_files.pop(self.target_files.index(tfile))
					failed_open_count += 1

		# Unless -O was specified, don't run the scan unless we are able to scan all specified files
		if failed_open_count > 0 and not self.skip_unopened:
			if failed_open_count > 1:
				plural = 's'
			else:
				plural = ''
			raise Exception("Failed to open %d file%s for scanning" % (failed_open_count, plural))

