import io
import os
import sys
import inspect
import argparse
import binwalk.common
import binwalk.config
import binwalk.plugin
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
		@extract     - Set to True to flag this result for extraction.

		Provide additional kwargs as necessary.
		Returns None.
		'''
		self.offset = 0
		self.description = ''
		self.file = None
		self.valid = True
		self.display = True
		self.extract = True

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

class Module(object):
	'''
	All module classes must be subclassed from this.
	'''
	# The module title, as displayed in help output
	TITLE = ""

	# A list of binwalk.module.ModuleOption command line options
	CLI = []

	# A list of binwalk.module.ModuleKwargs accepted by __init__
	KWARGS = []

	# A dictionary of module dependencies; all modules depend on binwalk.modules.configuration.Configuration
	DEPENDS = {'config' : 'Configuration'}

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
		self.errors = []
		self.results = []
		self.status = None
		self.name = self.__class__.__name__
		self.plugins = binwalk.plugin.Plugins(self)

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
	
		self.plugins.load_plugins()

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
		self.plugins.pre_scan_callbacks(self)

	def _plugins_post_scan(self):
		self.plugins.post_scan_callbacks(self)

	def _plugins_result(self, r):
		self.plugins.scan_callbacks(r)

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

	def result(self, r=None, **kwargs):
		'''
		Validates a result, stores it in self.results and prints it.
		Accepts the same kwargs as the binwalk.module.Result class.

		@r - An existing instance of binwalk.module.Result.

		Returns None.
		'''
		if r is None:
			r = Result(**kwargs)

		self.validate(r)
		self._plugins_result(r)

		if r.valid:
			self.results.append(r)

			# Update the progress status automatically if it is not being done manually by the module
			if r.file and not self.status.total:
				self.status.total = r.file.length
				self.status.completed = r.file.tell() - r.file.offset

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
		e.module = self

		self.errors.append(e)
		
		if e.exception:
			sys.stderr.write(e.module.__class__.__name__ + " Exception: " + str(e.exception) + "\n")
		elif e.description:
			sys.stderr.write(e.module.__class__.__name__ + " Error: " + e.description + "\n")

	def header(self):
		self.config.display.format_strings(self.HEADER_FORMAT, self.RESULT_FORMAT)
		if type(self.HEADER) == type([]):
			self.config.display.header(*self.HEADER)
		elif self.HEADER:
			self.config.display.header(self.HEADER)
	
	def footer(self):
		self.config.display.footer()
			
	def main(self, status):
		'''
		Responsible for calling self.init, initializing self.config.display, and calling self.run.

		Returns the value returned from self.run.
		'''
		self.status = status

		try:
			self.init()
		except KeyboardInterrupt as e:
			raise e
		except Exception as e:
			self.error(exception=e)
			return False

		try:
			self.config.display.format_strings(self.HEADER_FORMAT, self.RESULT_FORMAT)
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

class Status(object):
	
	def __init__(self, **kwargs):
		self.kwargs = kwargs
		self.clear()

	def clear(self):
		for (k,v) in iterator(self.kwargs):
			setattr(self, k, v)

class Modules(object):
	'''
	Main class used for running and managing modules.
	'''

	def __init__(self, *argv, **kargv):
		'''
		Class constructor.

		@argv  - List of command line options. Must not include the program name (e.g., sys.argv[1:]).
		@kargv - Keyword dictionary of command line options.

		Returns None.
		'''
		self.arguments = []
		self.loaded_modules = {}
		self.status = Status(completed=0, total=0)

		self._set_arguments(list(argv), kargv)

	def _set_arguments(self, argv=[], kargv={}):
		for (k,v) in iterator(kargv):
			k = self._parse_api_opt(k)
			if v not in [True, False, None]:
				argv.append("%s %s" % (k, v))
			else:
				argv.append(k)

		if not argv and not self.arguments:
			self.arguments = sys.argv[1:]
		elif argv:
			self.arguments = argv

	def _parse_api_opt(self, opt):
		# If the argument already starts with a hyphen, don't add hyphens in front of it
		if opt.startswith('-'):
			return opt
		# Short options are only 1 character
		elif len(opt) == 1:
			return '-' + opt
		else:
			return '--' + opt

	def list(self, attribute="run"):
		'''
		Finds all modules with the specified attribute.

		@attribute - The desired module attribute.

		Returns a list of modules that contain the specified attribute.
		'''
		modules = []

		for (name, module) in inspect.getmembers(binwalk.modules):
			if inspect.isclass(module) and hasattr(module, attribute):
				modules.append(module)

		return modules

	def help(self):
		help_string = "\nBinwalk v%s\nCraig Heffner, http://www.binwalk.org\n" % binwalk.config.Config.VERSION

		for obj in self.list(attribute="CLI"):
			if obj.CLI:
				help_string += "\n%s Options:\n" % obj.TITLE

				for module_option in obj.CLI:
					if module_option.long:
						long_opt = '--' + module_option.long
					
						if module_option.nargs > 0:
							optargs = "=%s" % module_option.dtype
						else:
							optargs = ""

						if module_option.short:
							short_opt = "-" + module_option.short + ","
						else:
							short_opt = "   "

						fmt = "    %%s %%s%%-%ds%%s\n" % (32-len(long_opt))
						help_string += fmt % (short_opt, long_opt, optargs, module_option.description)

		return help_string + "\n"

	def execute(self, *args, **kwargs):
		run_modules = []
		self._set_arguments(list(args), kwargs)

		for module in self.list():
			obj = self.run(module)
			if obj.enabled:
				run_modules.append(obj)
		return run_modules

	def run(self, module):
		obj = self.load(module)

		if isinstance(obj, binwalk.module.Module) and obj.enabled:
			obj.main(status=self.status)
			self.status.clear()

		# Add object to loaded_modules here, that way if a module has already been
		# loaded directly and is subsequently also listed as a dependency we don't waste
		# time loading it twice.
		self.loaded_modules[module] = obj
		return obj
			
	def load(self, module):
		kwargs = self.argv(module, argv=self.arguments)
		kwargs.update(self.dependencies(module))
		return module(**kwargs)
		
	def dependencies(self, module):
		kwargs = {}

		if hasattr(module, "DEPENDS"):
			for (kwarg, dependency) in iterator(module.DEPENDS):

				# The dependency module must be imported by binwalk.modules.__init__.py
				if hasattr(binwalk.modules, dependency):
					dependency = getattr(binwalk.modules, dependency)
				else:
					sys.stderr.write("WARNING: %s depends on %s which was not found in binwalk.modules.__init__.py\n" % (str(module), dependency))
					continue
				
				# No recursive dependencies, thanks
				if dependency == module:
					continue

				if not has_key(self.loaded_modules, dependency):
					# TODO: What to do if a dependency fails? Anything?
					self.run(dependency)
				kwargs[kwarg] = self.loaded_modules[dependency]
	
		return kwargs

	def argv(self, module, argv=sys.argv[1:]):
		'''
		Processes argv for any options specific to the specified module.
	
		@module - The module to process argv for.
		@argv   - A list of command line arguments (excluding argv[0]).

		Returns a dictionary of kwargs for the specified module.
		'''
		kwargs = {}
		last_priority = {}
		longs = []
		shorts = ""
		parser = argparse.ArgumentParser(add_help=False)

		if hasattr(module, "CLI"):

			for module_option in module.CLI:
				if not module_option.long:
					continue

				if module_option.nargs == 0:
					action = 'store_true'
				else:
					action = None

				if module_option.short:
					parser.add_argument('-' + module_option.short, '--' + module_option.long, action=action, dest=module_option.long)
				else:
					parser.add_argument('--' + module_option.long, action=action, dest=module_option.long)

			args, unknown = parser.parse_known_args(argv)
			args = args.__dict__

			for module_option in module.CLI:

				if module_option.type in [io.FileIO, argparse.FileType, binwalk.common.BlockFile]:

					for k in get_keys(module_option.kwargs):
						kwargs[k] = []
						for unk in unknown:
							if not unk.startswith('-'):
								kwargs[k].append(unk)

				elif has_key(args, module_option.long) and args[module_option.long] not in [None, False]:

					i = 0
					for (name, value) in iterator(module_option.kwargs):
						if not has_key(last_priority, name) or last_priority[name] <= module_option.priority:
							if module_option.nargs > i:
								value = args[module_option.long]
								i += 1

							last_priority[name] = module_option.priority

							# Do this manually as argparse doesn't seem to be able to handle hexadecimal values
							if module_option.type == int:
								kwargs[name] = int(value, 0)
							elif module_option.type == float:
								kwargs[name] = float(value)
							elif module_option.type == dict:
								if not has_key(kwargs, name):
									kwargs[name] = {}
								kwargs[name][len(kwargs[name])] = value
							elif module_option.type == list:
								if not has_key(kwargs, name):
									kwargs[name] = []
								kwargs[name].append(value)
							else:
								kwargs[name] = value
		else:
			raise Exception("binwalk.module.Modules.argv: %s has no attribute 'CLI'" % str(module))

		if not has_key(kwargs, 'enabled'):
			kwargs['enabled'] = False

		return kwargs
	
	def kwargs(self, module, kwargs):
		'''
		Processes a module's kwargs. All modules should use this for kwarg processing.

		@module - An instance of the module (e.g., self)
		@kwargs - The kwargs passed to the module

		Returns None.
		'''
		if hasattr(module, "KWARGS"):
			for module_argument in module.KWARGS:
				if has_key(kwargs, module_argument.name):
					arg_value = kwargs[module_argument.name]
				else:
					arg_value = module_argument.default

				setattr(module, module_argument.name, arg_value)

			for (k, v) in iterator(kwargs):
				if not hasattr(module, k):
					setattr(module, k, v)
		else:
			raise Exception("binwalk.module.Modules.process_kwargs: %s has no attribute 'KWARGS'" % str(module))


def process_kwargs(obj, kwargs):
	'''
	Convenience wrapper around binwalk.module.Modules.kwargs.

	@obj    - The class object (an instance of a sub-class of binwalk.module.Module).
	@kwargs - The kwargs provided to the object's __init__ method.

	Returns None.
	'''
	return Modules().kwargs(obj, kwargs)

def show_help(fd=sys.stdout):
	'''
	Convenience wrapper around binwalk.module.Modules.help.

	@fd - An object with a write method (e.g., sys.stdout, sys.stderr, etc).

	Returns None.
	'''
	fd.write(Modules().help())


