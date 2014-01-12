import binwalk.core.C
from binwalk.core.compat import *

class Magic(object):
    '''
    Minimalist Python wrapper around libmagic.
    '''

    LIBMAGIC_FUNCTIONS = [
            binwalk.core.C.Function(name="magic_open", type=int),
            binwalk.core.C.Function(name="magic_load", type=int),
            binwalk.core.C.Function(name="magic_buffer", type=str),
    ]

    MAGIC_CONTINUE          = 0x000020
    MAGIC_NO_CHECK_TEXT     = 0x020000
    MAGIC_NO_CHECK_APPTYPE  = 0x008000
    MAGIC_NO_CHECK_TOKENS   = 0x100000
    MAGIC_NO_CHECK_ENCODING = 0x200000
    
    MAGIC_FLAGS = MAGIC_NO_CHECK_TEXT | MAGIC_NO_CHECK_ENCODING | MAGIC_NO_CHECK_APPTYPE | MAGIC_NO_CHECK_TOKENS

    def __init__(self, magic_file=None, flags=0):
        if magic_file:
            self.magic_file = str2bytes(magic_file)
        else:
            self.magic_file = None

        self.libmagic = binwalk.core.C.Library("magic", self.LIBMAGIC_FUNCTIONS)

        self.magic_cookie = self.libmagic.magic_open(self.MAGIC_FLAGS | flags)
        self.libmagic.magic_load(self.magic_cookie, self.magic_file)

    def buffer(self, data):
        return self.libmagic.magic_buffer(self.magic_cookie, str2bytes(data), len(data))

