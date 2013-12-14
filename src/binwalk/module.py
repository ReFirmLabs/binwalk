import io
import sys
import inspect
import argparse
import binwalk.common
import binwalk.loader
from binwalk.compat import *

class ModuleOption(object):
	'''
	A container class that allows modules to declare command line options.
	'''

	def __init__(self, kwargs={}, nargs=0, priority=0, description="", short="", long="", type=str, dtype=""):
		'''
		Class constructor.

		@kwargs      - A dictionary of kwarg key-value pairs affected by this command line option.
		@nargs       - The number of arguments this option accepts (only 1 or 0 is currently supported).
		@priority    - A value from 0 to 100. Higher priorities will override kwarg values set by lower priority options.
		@description - A description to be displayed in the help output.
		@short       - The short option to use (optional).
		@long        - The long option to use (if None, this option will not be displayed in help output).
		@type        - The accepted data type (one of: io.FileIO/argparse.FileType/binwalk.common.BlockFile, list, str, int, float).
		@dtype       - The accepted data type, as displayed in the help output.

		Returns None.
		'''
		self.kwargs = kwargs
		self.nargs = nargs
		self.priority = priority
		self.description = description
		self.short = short
		self.long = long
		self.type = type
		self.dtype = str(dtype)

		if not self.dtype and self.type:
			self.dtype = str(self.type)

class ModuleKwarg(object):
		'''
		A container class allowing modules to specify their expected __init__ kwarg(s).
		'''

		def __init__(self, name="", default=None, description=""):
			'''
			Class constructor.
	
			@name        - Kwarg name.
			@default     - Default kwarg value.
			@description - Description string.

			Return None.
			'''
			self.name = name
			self.default = default
			self.description = description

class Result(object):
	'''
	Generic class for storing and accessing scan results.
	'''

	def __init__(self, **kwargs):
		'''
		Class constructor.

		@offset      - The file offset of the result.
		@description - The result description, as displayed to the user.
		@file        - The file object of the scanned file.
		@valid       - Set to True if the result if value, False if invalid.
		@display     - Set to True to display the result to the user, False to hide it.

		Provide additional kwargs as necessary.
		Returns None.
		'''
		self.offset = 0
		self.description = ''
		self.file = None
		self.valid = True
		self.display = True

		for (k, v) in iterator(kwargs):
			setattr(self, k, v)

class Error(Result):
	'''
	A subclass of binwalk.module.Result.
	'''
	
	def __init__(self, **kwargs):
		'''
		Accepts all the same kwargs as binwalk.module.Result, but the following are also added:

		@exception - In case of an exception, this is the exception object.

		Returns None.
		'''
		self.exception = None
		Result.__init__(self, **kwargs)

		if self.exception:
			sys.stderr.write("Exception: " + str(self.exception) + "\n")
		elif self.description:
			sys.stderr.write("Error: " + self.description + "\n")

class Module(object):
	'''
	All module classes must be subclassed from this.
	'''
	# The module name, as displayed in help output
	NAME = ""

	# A list of binwalk.module.ModuleOption command line options
	CLI = []

	# A list of binwalk.module.ModuleKwargs accepted by __init__
	KWARGS = []

	# A dictionary of module dependencies; all modules depend on binwalk.modules.configuration.Configuration
	DEPENDS = {}

	# Format string for printing the header during a scan
	HEADER_FORMAT = "%s\n"

	# Format string for printing each result during a scan 
	RESULT_FORMAT = "%.8d      %s\n"

	# The header to print during a scan.
	# Set to None to not print a header.
	# Note that this will be formatted per the HEADER_FORMAT format string.
	HEADER = ["OFFSET      DESCRIPTION"]

	# The attribute names to print during a scan, as provided to the self.results method.
	# Set to None to not print any results.
	# Note that these will be formatted per the RESULT_FORMAT format string.
	RESULT = ['offset', 'description']

	def __init__(self, dependency=False, **kwargs):
		# TODO: Instantiate plugins object
		# self.plugins = x
		self.errors = []
		self.results = []

		process_kwargs(self, kwargs)

		# If the module was loaded as a dependency, don't display or log any results
		if dependency:
			self.config.display.quiet = True
			self.config.display.log = None

		try:
			self.load()
		except KeyboardInterrupt as e:
			raise e
		except Exception as e:
			self.error(exception=e)

	def load(self):
		'''
		Invoked at module load time.
		May be overridden by the module sub-class.
		'''
		return None

	def init(self):
		'''
		Invoked prior to self.run.
		May be overridden by the module sub-class.

		Returns None.
		'''
		return None

	def run(self):
		'''
		Executes the main module routine.
		Must be overridden by the module sub-class.

		Returns True on success, False on failure.
		'''
		return False

	def validate(self, r):
		'''
		Validates the result.
		May be overridden by the module sub-class.

		@r - The result, an instance of binwalk.module.Result.

		Returns None.
		'''
		r.valid = True
		return None

	def _plugins_pre_scan(self):
		# plugins(self)
		return None

	def _plugins_post_scan(self):
		# plugins(self)
		return None

	def _plugins_callback(self, r):
		return None

	def _build_display_args(self, r):
		args = []

		if self.RESULT:
			if type(self.RESULT) != type([]):
				result = [self.RESULT]
			else:
				result = self.RESULT
	
			for name in result:
				args.append(getattr(r, name))
		
		return args

	def result(self, **kwargs):
		'''
		Validates a result, stores it in self.results and prints it.

		Accepts the same kwargs as the binwalk.module.Result class.

		Returns None.
		'''
		r = Result(**kwargs)

		self.validate(r)
		self._plugins_callback(r)

		if r.valid:
			self.results.append(r)
			if r.display:
				display_args = self._build_display_args(r)
				if display_args:
					self.config.display.result(*display_args)

	def error(self, **kwargs):
		'''
		Stores the specified error in self.errors.

		Accepts the same kwargs as the binwalk.module.Error class.

		Returns None.
		'''
		e = Error(**kwargs)
		self.errors.append(e)

	def header(self):
		self.config.display.format_strings(self.HEADER_FORMAT, self.RESULT_FORMAT)
		if type(self.HEADER) == type([]):
			self.config.display.header(*self.HEADER)
		elif self.HEADER:
			self.config.display.header(self.HEADER)
	
	def footer(self):
		self.config.display.footer()
			
	def main(self):
		'''
		Responsible for calling self.init, initializing self.config.display, and calling self.run.

		Returns the value returned from self.run.
		'''
		try:
			self.init()
		except KeyboardInterrupt as e:
			raise e
		except Exception as e:
			self.error(exception=e)
			return False

		self._plugins_pre_scan()

		try:
			retval = self.run()
		except KeyboardInterrupt as e:
			raise e
		except Exception as e:
			self.error(exception=e)
			return False

		self._plugins_post_scan()

		return retval


def process_kwargs(obj, kwargs):
	'''
	Convenience wrapper around binwalk.loader.Modules.kwargs.

	@obj    - The class object (an instance of a sub-class of binwalk.module.Module).
	@kwargs - The kwargs provided to the object's __init__ method.

	Returns None.
	'''
	return binwalk.loader.Modules().kwargs(obj, kwargs)

def show_help(fd=sys.stdout):
	'''
	Convenience wrapper around binwalk.loader.Modules.help.

	@fd - An object with a write method (e.g., sys.stdout, sys.stderr, etc).

	Returns None.
	'''
	fd.write(binwalk.loader.Modules().help())


