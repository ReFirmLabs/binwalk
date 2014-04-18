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
            raise Exception("Unknown return type: '%s'" % self.retype)

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

        return self.retval_converter(self.function(*args))
        
class Library(object):
    '''
    Class for loading the specified library via ctypes.
    '''

    def __init__(self, library, functions):
        '''
        Class constructor.

        @library   - Library name (e.g., 'magic' for libmagic).
        @functions - A dictionary of function names and their return types (e.g., {'magic_buffer' : str})

        Returns None.
        '''
        self.library = ctypes.cdll.LoadLibrary(self.find_library(library))
        if not self.library:
            raise Exception("Failed to load library '%s'" % library)

        for function in functions:    
            f = FunctionHandler(self.library, function)
            setattr(self, function.name, f.run)

    def find_library(self, library):
        '''
        Locates the specified library.

        @library - Library name (e.g., 'magic' for libmagic).
 
        Returns a string to be passed to ctypes.cdll.LoadLibrary.
        '''
        lib_path = None
        system_paths = {
            'linux'   : ['/usr/local/lib/lib%s.so' % library],
            'linux2'  : ['/usr/local/lib/lib%s.so' % library],
            'linux3'  : ['/usr/local/lib/lib%s.so' % library],
            'darwin'  : ['/opt/local/lib/lib%s.dylib' % library,
                        '/usr/local/lib/lib%s.dylib' % library,
                       ] + glob.glob('/usr/local/Cellar/lib%s/*/lib/lib%s.dylib' % (library, library)),

            'win32'   : ['%s.dll' % library]
        }

        lib_path = ctypes.util.find_library(library)

        # If ctypes failed to find the library, check the common paths listed in system_paths
        if not lib_path:
            for path in system_paths[sys.platform]:
                if os.path.exists(path):
                    lib_path = path
                    break

        if not lib_path:
            raise Exception("Failed to locate library '%s'" % library)

        binwalk.core.common.debug("Found library: " + lib_path)
        return lib_path

