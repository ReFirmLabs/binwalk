import os
import sys
import glob
import ctypes
import ctypes.util
from binwalk.core.compat import *

class Function(object):

	PY2CTYPES = {
			bytes	: ctypes.c_char_p,
			str		: ctypes.c_char_p,
			int		: ctypes.c_int,
			float	: ctypes.c_float,
			None	: ctypes.c_int,
	}

	RETVAL_CONVERTERS = {
			int 	: int,
			float	: float,
			str 	: bytes2str,
			bytes	: str2bytes,
	}
		
	def __init__(self, library, name, retype):
		self.function = getattr(library, name)
		self.retype = retype

		if has_key(self.PY2CTYPES, self.retype):
			self.function.restype = self.PY2CTYPES[self.retype]
			self.retval_converter = self.RETVAL_CONVERTERS[self.retype]
		else:
			raise Exception("Unknown return type: '%s'" % retype)

	def run(self, *args):
		args = list(args)

		for i in range(0, len(args)):
			if isinstance(args[i], str):
				args[i] = str2bytes(args[i])

		return self.retval_converter(self.function(*args))
		
class Library(object):

	def __init__(self, library, functions):
		self.library = ctypes.cdll.LoadLibrary(self.find_library(library))
		if not self.library:
			raise Exception("Failed to load library '%s'" % library)
				
		for (function, restype) in iterator(functions):
			f = Function(self.library, function, restype)
			setattr(self, function, f.run)

	def find_library(self, library):
		lib_path = None
		system_paths = {
			'linux'  : ['/usr/local/lib/lib%s.so' % library],
			'darwin' : ['/opt/local/lib/lib%s.dylib' % library,
						'/usr/local/lib/lib%s.dylib' % library,
					   ] + glob.glob('/usr/local/Cellar/lib%s/*/lib/lib%s.dylib' % (library, library)),

			'win32'  : ['%s.dll' % library]
		}

		lib_path = ctypes.util.find_library(library)

		if not lib_path:
			for path in system_paths[sys.platform]:
				if os.path.exists(path):
					lib_path = path
					break

		if not lib_path:
			raise Exception("Failed to locate library '%s'" % library)

		return lib_path

