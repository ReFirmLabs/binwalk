import os
import sys
import ctypes
import ctypes.util
import binwalk.core.common
import binwalk.core.libpaths
from binwalk.core.compat import *

class Function(object):
    '''
    Container class for defining library functions.
    '''
    def __init__(self, **kwargs):
        self.name = None
        self.type = int

        for (k, v) in iterator(kwargs):
            setattr(self, k, v)

class FunctionHandler(object):
    '''
    Class for abstracting function calls via ctypes and handling Python 2/3 compatibility issues.
    '''
    PY2CTYPES = {
            bytes   : ctypes.c_char_p,
            str     : ctypes.c_char_p,
            int     : ctypes.c_int,
            float   : ctypes.c_float,
            bool    : ctypes.c_int,
            None    : ctypes.c_int,
    }

    RETVAL_CONVERTERS = {
            None    : int,
            int     : int,
            float   : float,
            bool    : bool,
            str     : bytes2str,
            bytes   : str2bytes,
    }
        
    def __init__(self, library, function):
        '''
        Class constructor.

        @library - Library handle as returned by ctypes.cdll.LoadLibrary.
        @function - An instance of the binwalk.core.C.Function class.

        Returns None.
        '''
        self.name = function.name
        self.retype = function.type
        self.function = getattr(library, self.name)

        if has_key(self.PY2CTYPES, self.retype):
            self.function.restype = self.PY2CTYPES[self.retype]
            self.retval_converter = self.RETVAL_CONVERTERS[self.retype]
        else:
            self.function.restype = self.retype
            self.retval_converter = None
            #raise Exception("Unknown return type: '%s'" % self.retype)

    def run(self, *args):
        '''
        Executes the library function, handling Python 2/3 compatibility and properly converting the return type.

        @*args - Library function arguments.

        Returns the return value from the libraray function.
        '''
        args = list(args)

        # Python3 expects a bytes object for char *'s, not a str. 
        # This allows us to pass either, regardless of the Python version.
        for i in range(0, len(args)):
            if isinstance(args[i], str):
                args[i] = str2bytes(args[i])

        retval = self.function(*args)
        if self.retval_converter is not None:
            retval = self.retval_converter(retval)

        return retval
        
class Library(object):
    '''
    Class for loading the specified library via ctypes.
    '''

    def __init__(self, library, functions):
        '''
        Class constructor.

        @library   - Library name (e.g., 'magic' for libmagic), or a list of names.
        @functions - A dictionary of function names and their return types (e.g., {'magic_buffer' : str})

        Returns None.
        '''
        self.library = ctypes.cdll.LoadLibrary(self.find_library(library))
        if not self.library:
            raise Exception("Failed to load library '%s'" % library)

        for function in functions:    
            f = FunctionHandler(self.library, function)
            setattr(self, function.name, f.run)

    def check_if_library_exists(self, base_path, library):
        '''
        Checks if a library file exists at base_path.

        @base_path - Path to directory where library could be found.
        @library - Library name (e.g., 'magic' for libmagic), or a list of names.

        Returns a string containing the library path, or None.
        '''
        if sys.platform.startswith(('linux')) or sys.platform == 'cygwin':
            libprefix = 'lib'
            libext = '.so'
        elif sys.platform == 'darwin':
            libprefix = 'lib'
            libext = '.dylib'
        elif sys.platform == 'win32':
            libprefix = ''
            libext = '.dll'

        path = (base_path + '/' + libprefix + library + libext)
        binwalk.core.common.debug("Looking for library at %s" % path)
        if os.path.exists(path):
            return path
        else:
            return None


    def find_library(self, libraries):
        '''
        Locates the specified library.

        @libraries - Library name (e.g., 'magic' for libmagic), or a list of names.
 
        Returns a string to be passed to ctypes.cdll.LoadLibrary.
        '''
        lib_path = None

        if isinstance(libraries, str):
            libraries = [libraries]

        for library in libraries:
            # Search the compile-time specified paths first.
            for base_path in binwalk.core.libpaths.user_libs:
                lib_path = self.check_if_library_exists(base_path, library)
                if lib_path:
                    break

            # Search /usr/local/lib next if not on win32.
            if not lib_path and not sys.platform == 'win32':
                lib_path = self.check_if_library_exists('/usr/local/lib', library)

            # search local dir if on win32.
            if not lib_path and sys.platform == 'win32':
                lib_path = self.check_if_library_exists('', library)

            # If we failed to find the library, check the standard library search paths
            if not lib_path:
                lib_path = ctypes.util.find_library(library)

            # Use the first library that we can find
            if lib_path:
                binwalk.core.common.debug("Found library '%s' at: %s" % (library, lib_path))
                break
            else:
                binwalk.core.common.debug("Could not find library '%s'" % library)

        # If we still couldn't find the library, error out
        if not lib_path:
            raise Exception("Failed to locate libraries '%s'" % str(libraries))

        return lib_path

