# Core code relating to binwalk modules and supporting classes.
# In particular, the Module class (base class for all binwalk modules)
# and the Modules class (main class for managing and executing binwalk modules)
# are most critical.

import io
import os
import sys
import time
import inspect
import argparse
import traceback
from copy import copy
import binwalk
import binwalk.core.statuserver
import binwalk.core.common
import binwalk.core.settings
import binwalk.core.plugin
from binwalk.core.compat import *
from binwalk.core.exceptions import *


class Option(object):

    '''
    A container class that allows modules to declare command line options.
    '''

    def __init__(self, kwargs={}, priority=0, description="", short="", long="", type=None, dtype=None, hidden=False):
        '''
        Class constructor.

        @kwargs      - A dictionary of kwarg key-value pairs affected by this command line option.
        @priority    - A value from 0 to 100. Higher priorities will override kwarg values set by lower priority options.
        @description - A description to be displayed in the help output.
        @short       - The short option to use (optional).
        @long        - The long option to use (if None, this option will not be displayed in help output).
        @type        - The accepted data type (one of: io.FileIO/argparse.FileType/binwalk.core.common.BlockFile, list, str, int, float).
        @dtype       - The displayed accepted type string, to be shown in help output.
        @hidden      - If set to True, this option will not be displayed in the help output.

        Returns None.
        '''
        self.kwargs = kwargs
        self.priority = priority
        self.description = description
        self.short = short
        self.long = long
        self.type = type
        self.dtype = dtype
        self.hidden = hidden

        if not self.dtype and self.type:
            if self.type in [io.FileIO, argparse.FileType, binwalk.core.common.BlockFile]:
                self.dtype = 'file'
            elif self.type in [int, float, str]:
                self.dtype = self.type.__name__
            else:
                self.type = str
                self.dtype = str.__name__

    def convert(self, value, default_value):
        if self.type and (self.type.__name__ == self.dtype):
            # Be sure to specify a base of 0 for int() so that the base is
            # auto-detected
            if self.type == int:
                t = self.type(value, 0)
            else:
                t = self.type(value)
        elif default_value or default_value is False:
            t = default_value
        else:
            t = value

        return t


class Kwarg(object):

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


class Dependency(object):

    '''
    A container class for declaring module dependencies.
    '''

    def __init__(self, attribute="", name="", kwargs={}):
        self.attribute = attribute
        self.name = name
        self.kwargs = kwargs
        self.module = None


class Result(object):

    '''
    Generic class for storing and accessing scan results.
    '''

    def __init__(self, **kwargs):
        '''
        Class constructor.

        @offset      - The file offset of the result.
        @size        - Size of the result, if known.
        @description - The result description, as displayed to the user.
        @module      - Name of the module that generated the result.
        @file        - The file object of the scanned file.
        @valid       - Set to True if the result if value, False if invalid.
        @display     - Set to True to display the result to the user, False to hide it.
        @extract     - Set to True to flag this result for extraction.
        @plot        - Set to Flase to exclude this result from entropy plots.
        @name        - Name of the result found (None if not applicable or unknown).

        Provide additional kwargs as necessary.
        Returns None.
        '''
        self.offset = 0
        self.size = 0
        self.description = ''
        self.module = ''
        self.file = None
        self.valid = True
        self.display = True
        self.extract = True
        self.plot = True
        self.name = None

        for (k, v) in iterator(kwargs):
            setattr(self, k, v)


class Error(Result):

    '''
    A subclass of binwalk.core.module.Result.
    '''

    def __init__(self, **kwargs):
        '''
        Accepts all the same kwargs as binwalk.core.module.Result, but the following are also added:

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

    # A list of binwalk.core.module.Option command line options
    CLI = []

    # A list of binwalk.core.module.Kwargs accepted by __init__
    KWARGS = []

    # A list of default dependencies for all modules; do not override this unless you
    # understand the consequences of doing so.
    DEFAULT_DEPENDS = [
        Dependency(name='General',
                   attribute='config'),
        Dependency(name='Extractor',
                   attribute='extractor'),
    ]

    # A list of binwalk.core.module.Dependency instances that can be filled in
    # as needed by each individual module.
    DEPENDS = []

    # Format string for printing the header during a scan.
    # Must be set prior to calling self.header.
    HEADER_FORMAT = "%-12s  %-12s    %s\n"

    # Format string for printing each result during a scan.
    # Must be set prior to calling self.result.
    RESULT_FORMAT = "%-12d  0x%-12X  %s\n"

    # Format string for printing custom information in the verbose header output.
    # Must be set prior to calling self.header.
    VERBOSE_FORMAT = ""

    # The header to print during a scan.
    # Set to None to not print a header.
    # Note that this will be formatted per the HEADER_FORMAT format string.
    # Must be set prior to calling self.header.
    HEADER = ["DECIMAL", "HEXADECIMAL", "DESCRIPTION"]

    # The Result attribute names to print during a scan, as provided to the self.results method.
    # Set to None to not print any results.
    # Note that these will be formatted per the RESULT_FORMAT format string.
    # Must be set prior to calling self.result.
    RESULT = ["offset", "offset", "description"]

    # The custom data to print in the verbose header output.
    # Note that these will be formatted per the VERBOSE_FORMAT format string.
    # Must be set prior to calling self.header.
    VERBOSE = []

    # If set to True, the progress status will be automatically updated for each result
    # containing valid file and offset attributes.
    AUTO_UPDATE_STATUS = True

    # Modules with higher priorities are executed first
    PRIORITY = 5

    # Modules with a higher order are displayed first in help output
    ORDER = 5

    # Set to False if this is not a primary module (e.g., General, Extractor
    # modules)
    PRIMARY = True

    def __init__(self, parent, **kwargs):
        self.errors = []
        self.results = []

        self.parent = parent
        self.target_file_list = []
        self.status = None
        self.enabled = False
        self.previous_next_file_fp = None
        self.current_target_file_name = None
        self.name = self.__class__.__name__
        self.plugins = binwalk.core.plugin.Plugins(self)
        self.dependencies = self.DEFAULT_DEPENDS + self.DEPENDS

        process_kwargs(self, kwargs)

        self.plugins.load_plugins()

        try:
            self.load()
        except KeyboardInterrupt as e:
            raise e
        except Exception as e:
            self.error(exception=e)

        try:
            self.target_file_list = list(self.config.target_files)
        except AttributeError as e:
            pass

    def __enter__(self):
        return self

    def __exit__(self, x, z, y):
        return None

    def load(self):
        '''
        Invoked at module load time.
        May be overridden by the module sub-class.
        '''
        return None

    def unload(self):
        '''
        Invoked at module load time.
        May be overridden by the module sub-class.
        '''
        return None

    def reset(self):
        '''
        Invoked only for dependency modules immediately prior to starting a new primary module.
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

    def callback(self, r):
        '''
        Processes the result from all modules. Called for all dependency modules when a valid result is found.

        @r - The result, an instance of binwalk.core.module.Result.

        Returns None.
        '''
        return None

    def validate(self, r):
        '''
        Validates the result.
        May be overridden by the module sub-class.

        @r - The result, an instance of binwalk.core.module.Result.

        Returns None.
        '''
        r.valid = True
        return None

    def _plugins_pre_scan(self):
        self.plugins.pre_scan_callbacks(self)

    def _plugins_load_file(self, fp):
        try:
            self.plugins.load_file_callbacks(fp)
            return True
        except IgnoreFileException:
            return False

    def _plugins_new_file(self, fp):
        self.plugins.new_file_callbacks(fp)

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
                value = getattr(r, name)

                # Displayed offsets should be offset by the base address
                if name == 'offset':
                    value += self.config.base

                args.append(value)

        return args

    def _unload_dependencies(self):
        # Calls the unload method for all dependency modules.
        # These modules cannot be unloaded immediately after being run, as
        # they must persist until the module that depends on them is finished.
        # As such, this must be done separately from the Modules.run 'unload'
        # call.
        for dependency in self.dependencies:
            try:
                getattr(self, dependency.attribute).unload()
            except AttributeError:
                continue

    def next_file(self, close_previous=True):
        '''
        Gets the next file to be scanned (including pending extracted files, if applicable).
        Also re/initializes self.status.
        All modules should access the target file list through this method.
        '''
        fp = None

        # Ensure files are close to prevent IOError (too many open files)
        if close_previous:
            try:
                self.previous_next_file_fp.close()
            except KeyboardInterrupt as e:
                raise e
            except Exception:
                pass

        # Add any pending extracted files to the target_files list and reset
        # the extractor's pending file list
        self.target_file_list += self.extractor.pending

        # Reset all dependencies prior to continuing with another file.
        # This is particularly important for the extractor module, which must be reset
        # in order to reset its base output directory path for each file, and the
        # list of pending files.
        self.reset_dependencies()

        while self.target_file_list:
            next_target_file = self.target_file_list.pop(0)

            # Values in self.target_file_list are either already open files (BlockFile instances), or paths
            # to files that need to be opened for scanning.
            if isinstance(next_target_file, str) or isinstance(next_target_file, unicode):
                fp = self.config.open_file(next_target_file)
            else:
                fp = next_target_file

            if not fp:
                break
            else:
                if (self.config.file_name_filter(fp) == False or
                        self._plugins_load_file(fp) == False):
                    fp.close()
                    fp = None
                    continue
                else:
                    self.status.clear()
                    self.status.total = fp.length
                    break

        if fp is not None:
            self.current_target_file_name = fp.path
            self.status.fp = fp
        else:
            self.current_target_file_name = None
            self.status.fp = None

        self.previous_next_file_fp = fp

        self._plugins_new_file(fp)

        return fp

    def clear(self, results=True, errors=True):
        '''
        Clears results and errors lists.
        '''
        if results:
            self.results = []
        if errors:
            self.errors = []

    def result(self, r=None, **kwargs):
        '''
        Validates a result, stores it in self.results and prints it.
        Accepts the same kwargs as the binwalk.core.module.Result class.

        @r - An existing instance of binwalk.core.module.Result.

        Returns an instance of binwalk.core.module.Result.
        '''
        if r is None:
            r = Result(**kwargs)

        # Add the name of the current module to the result
        r.module = self.__class__.__name__

        # Any module that is reporting results, valid or not, should be marked
        # as enabled
        if not self.enabled:
            self.enabled = True
        self.validate(r)
        self._plugins_result(r)

        # Update the progress status automatically if it is not being done
        # manually by the module
        if r.offset and r.file and self.AUTO_UPDATE_STATUS:
            self.status.total = r.file.length
            self.status.completed = r.offset
            self.status.fp = r.file

        for dependency in self.dependencies:
            try:
                getattr(self, dependency.attribute).callback(r)
            except AttributeError:
                continue

        if r.valid:
            self.results.append(r)

            if r.display:
                display_args = self._build_display_args(r)
                if display_args:
                    self.config.display.format_strings(self.HEADER_FORMAT, self.RESULT_FORMAT)
                    self.config.display.result(*display_args)

        return r

    def error(self, **kwargs):
        '''
        Stores the specified error in self.errors.

        Accepts the same kwargs as the binwalk.core.module.Error class.

        Returns None.
        '''
        exception_header_width = 100

        e = Error(**kwargs)
        e.module = self.__class__.__name__

        self.errors.append(e)

        if e.exception:
            sys.stderr.write("\n" + e.module + " Exception: " + str(e.exception) + "\n")
            sys.stderr.write("-" * exception_header_width + "\n")
            traceback.print_exc(file=sys.stderr)
            sys.stderr.write("-" * exception_header_width + "\n\n")
        elif e.description:
            sys.stderr.write("\n" + e.module + " Error: " + e.description + "\n\n")

    def header(self):
        '''
        Displays the scan header, as defined by self.HEADER and self.HEADER_FORMAT.

        Returns None.
        '''
        self.config.display.format_strings(self.HEADER_FORMAT, self.RESULT_FORMAT)
        self.config.display.add_custom_header(self.VERBOSE_FORMAT, self.VERBOSE)

        if type(self.HEADER) == type([]):
            self.config.display.header(*self.HEADER, file_name=self.current_target_file_name)
        elif self.HEADER:
            self.config.display.header(self.HEADER, file_name=self.current_target_file_name)

    def footer(self):
        '''
        Displays the scan footer.

        Returns None.
        '''
        self.config.display.footer()

    def reset_dependencies(self):
        # Reset all dependency modules
        for dependency in self.dependencies:
            if hasattr(self, dependency.attribute):
                getattr(self, dependency.attribute).reset()

    def main(self):
        '''
        Responsible for calling self.init, initializing self.config.display, and calling self.run.

        Returns the value returned from self.run.
        '''
        self.status = self.parent.status
        self.modules = self.parent.executed_modules

        # A special exception for the extractor module, which should be allowed to
        # override the verbose setting, e.g., if --matryoshka has been
        # specified
        if hasattr(self, "extractor") and self.extractor.config.verbose:
            self.config.verbose = self.config.display.verbose = True

        if not self.config.files:
            binwalk.core.common.debug("No target files specified, module %s terminated" % self.name)
            return False

        self.reset_dependencies()

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

    '''
    Class used for tracking module status (e.g., % complete).
    '''

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.clear()

    def clear(self):
        for (k, v) in iterator(self.kwargs):
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
        self.executed_modules = {}
        self.default_dependency_modules = {}
        self.status = Status(completed=0, total=0, fp=None, running=False, shutdown=False, finished=False)
        self.status_server_started = False
        self.status_service = None

        self._set_arguments(list(argv), kargv)

    def cleanup(self):
        if self.status_service:
            self.status_service.server.socket.shutdown(1)
            self.status_service.server.socket.close()

    def __enter__(self):
        return self

    def __exit__(self, t, v, b):
        self.cleanup()

    def _set_arguments(self, argv=None, kargv=None):
        if kargv:
            for (k, v) in iterator(kargv):
                    k = self._parse_api_opt(k)
                    if v is not True and v is not False and v is not None:
                        if not isinstance(v, list):
                            v = [v]
                        for value in v:
                            if not isinstance(value, str):
                                value = str(bytes2str(value))
                            argv.append(k)
                            argv.append(value)
                    else:
                        # Only append if the value is True; this allows for toggling values
                        # by the function call.
                        if v:
                            argv.append(k)

        if not argv and not self.arguments:
            self.arguments = sys.argv[1:]
        elif argv:
            self.arguments = argv

    def _parse_api_opt(self, opt):
        # If the argument already starts with a hyphen, don't add hyphens in
        # front of it
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

        Returns a list of modules that contain the specified attribute, in the order they should be executed.
        '''
        import binwalk.modules
        modules = {}

        for (name, module) in inspect.getmembers(binwalk.modules):
            if inspect.isclass(module) and hasattr(module, attribute):
                modules[module] = module.PRIORITY

        # user-defined modules
        import imp
        user_modules = binwalk.core.settings.Settings().user.modules
        for file_name in os.listdir(user_modules):
            if not file_name.endswith('.py'):
                continue
            module_name = file_name[:-3]
            try:
                user_module = imp.load_source(module_name, os.path.join(user_modules, file_name))
            except KeyboardInterrupt as e:
                raise e
            except Exception as e:
                binwalk.core.common.warning("Error loading module '%s': %s" % (file_name, str(e)))

            for (name, module) in inspect.getmembers(user_module):
                if inspect.isclass(module) and hasattr(module, attribute):
                    modules[module] = module.PRIORITY

        return sorted(modules, key=modules.get, reverse=True)

    def help(self):
        '''
        Generates formatted help output.

        Returns the help string.
        '''
        modules = {}
        help_string = "\n"
        help_string += "Binwalk v%s\n" % binwalk.__version__
        help_string += "Craig Heffner, ReFirmLabs\n"
        help_string += "https://github.com/ReFirmLabs/binwalk\n"
        help_string += "\n"
        help_string += "Usage: binwalk [OPTIONS] [FILE1] [FILE2] [FILE3] ...\n"

        # Build a dictionary of modules and their ORDER attributes.
        # This makes it easy to sort modules by their ORDER attribute for
        # display.
        for module in self.list(attribute="CLI"):
            if module.CLI:
                modules[module] = module.ORDER

        for module in sorted(modules, key=modules.get, reverse=True):
            help_string += "\n%s Options:\n" % module.TITLE

            for module_option in module.CLI:
                if module_option.long and not module_option.hidden:
                    long_opt = '--' + module_option.long

                    if module_option.dtype:
                        optargs = "=<%s>" % module_option.dtype
                    else:
                        optargs = ""

                    if module_option.short:
                        short_opt = "-" + module_option.short + ","
                    else:
                        short_opt = "   "

                    fmt = "    %%s %%s%%-%ds%%s\n" % (25 - len(long_opt))
                    help_string += fmt % (short_opt, long_opt, optargs, module_option.description)

        return help_string + "\n"

    def execute(self, *args, **kwargs):
        '''
        Executes all appropriate modules according to the options specified in args/kwargs.

        Returns a list of executed module objects.
        '''
        run_modules = []
        orig_arguments = self.arguments

        if args or kwargs:
            self._set_arguments(list(args), kwargs)

        # Run all modules
        for module in self.list():
            obj = self.run(module)

        # Add all loaded modules that marked themselves as enabled to the
        # run_modules list
        for (module, obj) in iterator(self.executed_modules):
            # Report the results if the module is enabled and if it is a
            # primary module or if it reported any results/errors
            if obj.enabled and (obj.PRIMARY or obj.results or obj.errors):
                run_modules.append(obj)

        self.arguments = orig_arguments

        return run_modules

    def run(self, module, dependency=False, kwargs={}):
        '''
        Runs a specific module.
        '''
        try:
            obj = self.load(module, kwargs)

            if isinstance(obj, binwalk.core.module.Module) and obj.enabled:
                obj.main()
                self.status.clear()

            # If the module is not being loaded as a dependency, add it to the executed modules dictionary.
            # This is used later in self.execute to determine which objects
            # should be returned.
            if not dependency:
                self.executed_modules[module] = obj

                # The unload method tells the module that we're done with it, and gives it a chance to do
                # any cleanup operations that may be necessary. We still retain
                # the object instance in self.executed_modules.
                obj._unload_dependencies()
                obj.unload()
        except KeyboardInterrupt as e:
            # Tell the status server to shut down, and give it time to clean
            # up.
            if self.status.running:
                self.status.shutdown = True
                while not self.status.finished:
                    time.sleep(0.1)
            raise e

        return obj

    def load(self, module, kwargs={}):
        argv = self.argv(module, argv=self.arguments)
        argv.update(kwargs)
        argv.update(self.dependencies(module, argv['enabled']))
        return module(self, **argv)

    def dependencies(self, module, module_enabled):
        import binwalk.modules
        attributes = {}

        for dependency in module.DEFAULT_DEPENDS + module.DEPENDS:

            # The dependency module must be imported by
            # binwalk.modules.__init__.py
            if hasattr(binwalk.modules, dependency.name):
                dependency.module = getattr(binwalk.modules, dependency.name)
            else:
                raise ModuleException("%s depends on %s which was not found in binwalk.modules.__init__.py\n" % (str(module), dependency.name))

            # No recursive dependencies, thanks
            if dependency.module == module:
                continue

            # Only load dependencies with custom kwargs from modules that are enabled, else madness ensues.
            # Example: Heursitic module depends on entropy module, and sets entropy kwargs to contain 'enabled' : True.
            #          Without this check, an entropy scan would always be run, even if -H or -E weren't specified!
            #
            # Modules that are not enabled (e.g., extraction module) can load any dependency as long as they don't
            # set any custom kwargs for those dependencies.
            if module_enabled or not dependency.kwargs:
                depobj = self.run(dependency.module, dependency=True, kwargs=dependency.kwargs)

            # If a dependency failed, consider this a non-recoverable error and
            # raise an exception
            if depobj.errors:
                raise ModuleException("Failed to load " + dependency.name + " module")
            else:
                attributes[dependency.attribute] = depobj

        return attributes

    def argv(self, module, argv=sys.argv[1:]):
        '''
        Processes argv for any options specific to the specified module.

        @module - The module to process argv for.
        @argv   - A list of command line arguments (excluding argv[0]).

        Returns a dictionary of kwargs for the specified module.
        '''
        kwargs = {'enabled': False}
        last_priority = {}
        parser = argparse.ArgumentParser(add_help=False)
        # Hack: This allows the ListActionParser class to correllate short options to long options.
        # There is probably a built-in way to do this in the
        # argparse.ArgumentParser class?
        parser.short_to_long = {}

        # Must build arguments from all modules so that:
        #
        #    1) Any conflicting arguments will raise an exception
        #    2) The only unknown arguments will be the target files, making them
        #       easy to identify
        for m in self.list(attribute="CLI"):

            for module_option in m.CLI:

                parser_args = []
                parser_kwargs = {}

                if not module_option.long:
                    continue

                if module_option.short:
                    parser_args.append('-' + module_option.short)
                parser_args.append('--' + module_option.long)
                parser_kwargs['dest'] = module_option.long

                if module_option.type is None:
                    parser_kwargs['action'] = 'store_true'
                elif module_option.type is list:
                    parser_kwargs['action'] = 'append'
                    parser.short_to_long[
                        module_option.short] = module_option.long

                parser.add_argument(*parser_args, **parser_kwargs)

        args, unknown = parser.parse_known_args(argv)
        args = args.__dict__

        # Only add parsed options pertinent to the requested module
        for module_option in module.CLI:

            if module_option.type == binwalk.core.common.BlockFile:

                for k in get_keys(module_option.kwargs):
                    kwargs[k] = []
                    for unk in unknown:
                        kwargs[k].append(unk)

            elif has_key(args, module_option.long) and args[module_option.long] not in [None, False]:

                # Loop through all the kwargs for this command line option
                for (name, default_value) in iterator(module_option.kwargs):

                    # If this kwarg has not been previously processed, or if its priority is equal to or
                    # greater than the previously processed kwarg's priority,
                    # then let's process it.
                    if not has_key(last_priority, name) or last_priority[name] <= module_option.priority:

                        # Track the priority for future iterations that may
                        # process the same kwarg name
                        last_priority[name] = module_option.priority

                        try:
                            kwargs[name] = module_option.convert(args[module_option.long], default_value)
                        except KeyboardInterrupt as e:
                            raise e
                        except Exception as e:
                            raise ModuleException("Invalid usage: %s" % str(e))

        binwalk.core.common.debug("%s :: %s => %s" % (module.TITLE, str(argv), str(kwargs)))
        return kwargs

    def kwargs(self, obj, kwargs):
        '''
        Processes a module's kwargs. All modules should use this for kwarg processing.

        @obj    - An instance of the module (e.g., self)
        @kwargs - The kwargs passed to the module

        Returns None.
        '''
        if hasattr(obj, "KWARGS"):
            for module_argument in obj.KWARGS:
                if has_key(kwargs, module_argument.name):
                    arg_value = kwargs[module_argument.name]
                else:
                    arg_value = copy(module_argument.default)

                setattr(obj, module_argument.name, arg_value)

            for (k, v) in iterator(kwargs):
                if not hasattr(obj, k):
                    setattr(obj, k, v)
        else:
            raise Exception("binwalk.core.module.Modules.process_kwargs: %s has no attribute 'KWARGS'" % str(obj))

    def status_server(self, port):
        '''
        Starts the progress bar TCP service on the specified port.
        This service will only be started once per instance, regardless of the
        number of times this method is invoked.

        Failure to start the status service is considered non-critical; that is,
        a warning will be displayed to the user, but normal operation will proceed.
        '''
        if self.status_server_started == False:
            self.status_server_started = True
            try:
                self.status_service = binwalk.core.statuserver.StatusServer(port, self)
            except Exception as e:
                binwalk.core.common.warning("Failed to start status server on port %d: %s" % (port, str(e)))


def process_kwargs(obj, kwargs):
    '''
    Convenience wrapper around binwalk.core.module.Modules.kwargs.

    @obj    - The class object (an instance of a sub-class of binwalk.core.module.Module).
    @kwargs - The kwargs provided to the object's __init__ method.

    Returns None.
    '''
    with Modules() as m:
        kwargs = m.kwargs(obj, kwargs)
    return kwargs


def show_help(fd=sys.stdout):
    '''
    Convenience wrapper around binwalk.core.module.Modules.help.

    @fd - An object with a write method (e.g., sys.stdout, sys.stderr, etc).

    Returns None.
    '''
    with Modules() as m:
        fd.write(m.help())
