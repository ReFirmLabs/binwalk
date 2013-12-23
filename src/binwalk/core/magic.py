import ctypes
import ctypes.util
import binwalk.core.C
from binwalk.core.compat import *

class Magic(object):

	LIBMAGIC_FUNCTIONS = {
			"magic_open"	: int,
			"magic_load"	: int,
			"magic_buffer"	: str,
	}

	MAGIC_NO_CHECK_TEXT 	= 0x020000
	MAGIC_NO_CHECK_APPTYPE 	= 0x008000
	MAGIC_NO_CHECK_TOKENS 	= 0x100000
	MAGIC_NO_CHECK_ENCODING = 0x200000

	MAGIC_FLAGS = MAGIC_NO_CHECK_TEXT | MAGIC_NO_CHECK_ENCODING | MAGIC_NO_CHECK_APPTYPE | MAGIC_NO_CHECK_TOKENS

	def __init__(self, magic_file=None):
		if magic_file:
			self.magic_file = str2bytes(magic_file)

		self.libmagic = binwalk.core.C.Library('magic', self.LIBMAGIC_FUNCTIONS)

		self.magic_cookie = self.libmagic.magic_open(self.MAGIC_FLAGS)
		self.libmagic.magic_load(self.magic_cookie, self.magic_file)

	def buffer(self, data):
		return self.libmagic.magic_buffer(self.magic_cookie, str2bytes(data), len(data))

if __name__ == "__main__":
	magic = Magic()
	print (magic.buffer("This is my voice on TV."))
