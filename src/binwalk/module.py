import io
import sys
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

def list_modules():
	pass

def process_argv(module, config=None, argv=sys.argv[1:]):
	'''
	Processes argv for any options specific to the specified module.

	@module - The module to process argv for.
	@config - An instance of the binwalk.modules.configuration.Configuration class.
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
							kwargs[name] = int(kwargs[name], 0)
						elif module_option.type == float:
							kwargs[name] = float(kwargs[name])
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
		raise Exception("binwalk.module.process_argv: %s has no attribute 'CLI'" % str(module))

	if config is not None and not has_key(kwargs, 'config'):
		kwargs['config'] = config
		
	return kwargs
	

def process_kwargs(module, kwargs):
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

		if has_key(kwargs, 'config'):
			setattr(module, 'config', kwargs['config'])
	else:
		raise Exception("binwalk.module.parse_module_kwargs: %s has no attribute 'KWARGS'" % str(module))

