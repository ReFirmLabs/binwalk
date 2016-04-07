import os
import sys
import glob
import ctypes
import ctypes.util
import binwalk.core.common
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
        self.settings = binwalk.core.settings.Settings()
        self.library = ctypes.cdll.LoadLibrary(self.find_library(library))
        if not self.library:
            raise Exception("Failed to load library '%s'" % library)

        for function in functions:    
            f = FunctionHandler(self.library, function)
            setattr(self, function.name, f.run)

    def find_library(self, libraries):
        '''
        Locates the specified library.

        @libraries - Library name (e.g., 'magic' for libmagic), or a list of names.
 
        Returns a string to be passed to ctypes.cdll.LoadLibrary.
        '''
        lib_path = None

        prefix = binwalk.core.common.get_libs_path()
        
        if isinstance(libraries, str):
            libraries = [libraries]

        for library in libraries:
            system_paths = {
                'linux'   : [os.path.join(prefix, 'lib%s.so' % library), '/usr/local/lib/lib%s.so' % library],
                'cygwin'  : [os.path.join(prefix, 'lib%s.so' % library), '/usr/local/lib/lib%s.so' % library],
                'win32'   : [os.path.join(prefix, 'lib%s.dll' % library), '%s.dll' % library],
                'darwin'  : [os.path.join(prefix, 'lib%s.dylib' % library),
                             '/opt/local/lib/lib%s.dylib' % library,
                             '/usr/local/lib/lib%s.dylib' % library,
                            ] + glob.glob('/usr/local/Cellar/*%s*/*/lib/lib%s.dylib' % (library, library)),
            }

            for i in range(2, 4):
                system_paths['linux%d' % i] = system_paths['linux']

            # Search the common install directories first; these are usually not in the library search path
            # Search these *first*, since a) they are the most likely locations and b) there may be a
            # discrepency between where ctypes.util.find_library and ctypes.cdll.LoadLibrary search for libs.
            for path in system_paths[sys.platform]:
                binwalk.core.common.debug("Searching for '%s'" % path)
                if os.path.exists(path):
                    lib_path = path
                    break

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

