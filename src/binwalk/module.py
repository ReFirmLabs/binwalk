import io
import sys
import inspect
import argparse
import binwalk.common
from binwalk.compat import *

class ModuleOption(object):

	def __init__(self, kwargs={}, nargs=0, priority=0, description="", short="", long="", type=str):
		'''
		Class constructor.

		@kwargs      - A dictionary of kwarg key-value pairs affected by this command line option.
		@nargs       - The number of arguments this option accepts (only 1 or 0 is currently supported).
		@priority    - A value from 0 to 100. Higher priorities will override kwarg values set by lower priority options.
		@description - A description to be displayed in the help output.
		@short       - The short option to use (optional).
		@long        - The long option to use (if None, this option will not be displayed in help output).
		@type        - The accepted data type (one of: io.FileIO/argparse.FileType/binwalk.common.BlockFile, list, str, int, float).
		'''
		self.kwargs = kwargs
		self.nargs = nargs
		self.priority = priority
		self.description = description
		self.short = short
		self.long = long
		self.type = type

class ModuleKwarg(object):
		
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


def process_kwargs(module, kwargs):
	return Modules(dummy=True).kwargs(module, kwargs)

def show_help():
	print Modules(dummy=True).help()

class Modules(object):

	def __init__(self, dummy=False):
		self.config = None
		self.dependency_results = {}

		if not dummy:
			from binwalk.modules.configuration import Configuration
			self.config = self.load(Configuration)

	def list(self, attribute="run"):
		import binwalk.modules

		objects = []

		for (name, obj) in inspect.getmembers(binwalk.modules):
			if inspect.isclass(obj) and hasattr(obj, attribute):
				objects.append(obj)
		return objects

	def help(self):
		help_string = ""

		for obj in self.list(attribute="CLI"):
			help_string += "\n%s Options:\n" % obj.NAME

			for module_option in obj.CLI:
				if module_option.long:
					long_opt = '--' + module_option.long
					
					if module_option.nargs > 0:
						optargs = "=%s" % str(module_option.type)
					else:
						optargs = ""

					if module_option.short:
						short_opt = "-" + module_option.short + ","
					else:
						short_opt = "   "

					fmt = "    %%s %%s%%-%ds%%s\n" % (32-len(long_opt))
					help_string += fmt % (short_opt, long_opt, optargs, module_option.description)

		return help_string

	def execute(self):
		results = {}
		for module in self.list():
			result = self.run(module)
			if result is not None:
				results[module] = result
		return results

	def run(self, module):
		results = None
		obj = self.load(module)

		if obj.enabled:
			try:
				results = obj.run()
			except AttributeError as e:
				print("WARNING:", e)

		return results
			
	def load(self, module):
		kwargs = self.argv(module)
		kwargs.update(self.dependencies(module))
		return module(**kwargs)

	def dependencies(self, module):
		kwargs = {}

		if hasattr(module, "DEPENDS"):
			# Disable output when modules are loaded as dependencies
			orig_log = self.config.display.log
			orig_quiet = self.config.display.quiet
			self.config.display.log = False
			self.config.display.quiet = True

			for (kwarg, mod) in iterator(module.DEPENDS):
				if not has_key(self.dependency_results, mod):
					self.dependency_results[mod] = self.run(mod)
				kwargs[kwarg] = self.dependency_results[mod]
	
			self.config.display.log = orig_log	
			self.config.display.quiet = orig_quiet

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
			raise Exception("binwalk.module.argv: %s has no attribute 'CLI'" % str(module))

		if self.config is not None and not has_key(kwargs, 'config'):
			kwargs['config'] = self.config
				
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

			if not hasattr(module, 'enabled'):
				setattr(module, 'enabled', False)
		else:
			raise Exception("binwalk.module.process_kwargs: %s has no attribute 'KWARGS'" % str(module))

