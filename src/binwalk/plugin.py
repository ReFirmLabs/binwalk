import os
import sys
import imp
import binwalk.config
from binwalk.compat import *

class Plugins:
	'''
	Class to load and call plugin callback functions, handled automatically by Binwalk.scan / Binwalk.single_scan.
	An instance of this class is available during a scan via the Binwalk.plugins object.

	Each plugin must be placed in the user or system plugins directories, and must define a class named 'Plugin'.
	The Plugin class constructor (__init__) is passed one argument, which is the current instance of the Binwalk class.
	The Plugin class constructor is called once prior to scanning a file or set of files.
	The Plugin class destructor (__del__) is called once after scanning all files.

	The Plugin class can define one or all of the following callback methods:

		o pre_scan(self, fd)
		  This method is called prior to running a scan against a file. It is passed the file object of
		  the file about to be scanned.

		o pre_parser(self, result)
		  This method is called every time any result - valid or invalid - is found in the file being scanned.
		  It is passed a dictionary with one key ('description'), which contains the raw string returned by libmagic.
		  The contents of this dictionary key may be modified as necessary by the plugin.

		o callback(self, results)
		  This method is called every time a valid result is found in the file being scanned. It is passed a 
		  dictionary of results. This dictionary is identical to that passed to Binwalk.single_scan's callback 
		  function, and its contents may be modified as necessary by the plugin.

		o post_scan(self, fd)
		  This method is called after running a scan against a file, but before the file has been closed.
		  It is passed the file object of the scanned file.

	Valid return values for all plugin callbacks are (PLUGIN_* values may be OR'd together):

		PLUGIN_CONTINUE     - Do nothing, continue the scan normally.
		PLUGIN_NO_EXTRACT   - Do not preform data extraction.
		PLUGIN_NO_DISPLAY   - Ignore the result(s); they will not be displayed or further processed.
		PLUGIN_STOP_PLUGINS - Do not call any other plugins.
		PLUGIN_TERMINATE    - Terminate the scan.
		None                - The same as PLUGIN_CONTINUE.

	Values returned by pre_scan affect all results during the scan of that particular file.
	Values returned by callback affect only that specific scan result.
	Values returned by post_scan are ignored since the scan of that file has already been completed.

	By default, all plugins are loaded during binwalk signature scans. Plugins that wish to be disabled by 
	default may create a class variable named 'ENABLED' and set it to False. If ENABLED is set to False, the
	plugin will only be loaded if it is explicitly named in the plugins whitelist.

	Simple example plugin:

		from binwalk.plugins import *

		class Plugin:

			# Set to False to have this plugin disabled by default.
			ENABLED = True

			def __init__(self):
				self.binwalk = binwalk
				print 'Scanning initialized!'

			def __del__(self):
				print 'Scanning complete!'

			def pre_scan(self, fd):
				print 'About to scan', fd.name
				return PLUGIN_CONTINUE

			def callback(self, results):
				print 'Got a result:', results['description']
				return PLUGIN_CONTINUE

			def post_scan(self, fd):
				print 'Done scanning', fd.name 
				return PLUGIN_CONTINUE
	'''

	RESULT = 'result'
	PRESCAN = 'pre_scan'
	POSTSCAN = 'post_scan'
	PLUGIN = 'Plugin'
	MODULE_EXTENSION = '.py'

	def __init__(self, whitelist=[], blacklist=[]):
		self.config = binwalk.config.Config()
		self.result = []
		self.pre_scan = []
		self.pre_parser = []
		self.post_scan = []
		self.whitelist = whitelist
		self.blacklist = blacklist

	def __del__(self):
		pass

	def __enter__(self):
		return self

	def __exit__(self, t, v, traceback):
		pass

	def _call_plugins(self, callback_list, arg):
		retval = PLUGIN_CONTINUE

		for callback in callback_list:
			if (retval & PLUGIN_STOP_PLUGINS):
				break

			try:
				val = callback(arg)
				if val is not None:
					retval |= val
			except KeyboardInterrupt as e:
				raise e
			except Exception as e:
				sys.stderr.write("WARNING: %s.%s failed: %s\n" % (callback.__module__, callback.__name__, e))

		return retval

	def list_plugins(self):
		'''
		Obtain a list of all user and system plugin modules.

		Returns a dictionary of:

			{
				'user'		: {
							'modules' 	: [list, of, module, names],
							'descriptions'	: {'module_name' : 'module pydoc string'},
							'enabled'       : {'module_name' : True},
							'path'    	: "path/to/module/plugin/directory"
				},
				'system'	: {
							'modules' 	: [list, of, module, names],
							'descriptions'	: {'module_name' : 'module pydoc string'},
							'enabled'       : {'module_name' : True},
							'path'    	: "path/to/module/plugin/directory"
				}
			}
		'''

		plugins = {
			'user'   : {
					'modules' 	: [],
					'descriptions'	: {},
					'enabled'       : {},
					'path'    	: None,
			},
			'system' : {
					'modules' 	: [],
					'descriptions'	: {},
					'enabled'       : {},
					'path'    	: None,
			}
		}

		for key in plugins.keys():
			plugins[key]['path'] = self.config.paths[key][self.config.PLUGINS]

			for file_name in os.listdir(plugins[key]['path']):
				if file_name.endswith(self.MODULE_EXTENSION):
					module = file_name[:-len(self.MODULE_EXTENSION)]
					if module in self.blacklist:
						continue
					else:
						plugin = imp.load_source(module, os.path.join(plugins[key]['path'], file_name))
						plugin_class = getattr(plugin, self.PLUGIN)

						try:
							enabled = plugin_class.ENABLED
						except KeyboardInterrupt as e:
							raise e
						except Exception as e:
							enabled = True
						
						plugins[key]['enabled'][module] = enabled

						plugins[key]['modules'].append(module)
						
						try:
							plugins[key]['descriptions'][module] = plugin_class.__doc__.strip().split('\n')[0]
						except KeyboardInterrupt as e:
							raise e
						except Exception as e:
							plugins[key]['descriptions'][module] = 'No description'
		return plugins

	def _load_plugins(self):
		plugins = self.list_plugins()
		self._load_plugin_modules(plugins['user'])
		self._load_plugin_modules(plugins['system'])

	def _load_plugin_modules(self, plugins):
		for module in plugins['modules']:
			file_path = os.path.join(plugins['path'], module + self.MODULE_EXTENSION)

			try:
				plugin = imp.load_source(module, file_path)
				plugin_class = getattr(plugin, self.PLUGIN)

				try:
					# If this plugin is disabled by default and has not been explicitly white listed, ignore it
					if plugin_class.ENABLED == False and module not in self.whitelist:
						continue
				except KeyboardInterrupt as e:
					raise e
				except Exception as e:
					pass

				class_instance = plugin_class()

				try:
					self.result.append(getattr(class_instance, self.RESULT))
				except KeyboardInterrupt as e:
					raise e
				except Exception as e:
					pass

				try:
					self.pre_scan.append(getattr(class_instance, self.PRESCAN))
				except KeyboardInterrupt as e:
					raise e
				except Exception as e:
					pass

				try:
					self.post_scan.append(getattr(class_instance, self.POSTSCAN))
				except KeyboardInterrupt as e:
					raise e
				except Exception as e:
					pass
							
			except KeyboardInterrupt as e:
				raise e
			except Exception as e:
				sys.stderr.write("WARNING: Failed to load plugin module '%s': %s\n" % (module, str(e)))

	def _pre_scan_callbacks(self, obj):
		return self._call_plugins(self.pre_scan, obj)

	def _post_scan_callbacks(self, obj):
		return self._call_plugins(self.post_scan, obj)

	def _result_callbacks(self, obj):
		return self._call_plugins(self.result, obj)

