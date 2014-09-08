# Python wrapper for the libmagic library.
# Although libmagic comes with its own wrapper, there are compatibility issues with older libmagic versions
# as well as unofficial libmagic Python wrappers, so it's easier to just have our own wrapper.

import binwalk.core.C
import binwalk.core.common
from ctypes import *
from binwalk.core.compat import *

class magic_set(Structure):
    pass
magic_set._fields_ = []
magic_t = POINTER(magic_set)

class Magic(object):
    '''
    Minimalist Python wrapper around libmagic.
    '''

    LIBMAGIC_FUNCTIONS = [
            binwalk.core.C.Function(name="magic_open", type=magic_t),
            binwalk.core.C.Function(name="magic_close", type=int),
            binwalk.core.C.Function(name="magic_load", type=int),
            binwalk.core.C.Function(name="magic_buffer", type=str),
    ]

    MAGIC_CONTINUE          = 0x000020
    MAGIC_NO_CHECK_TEXT     = 0x020000
    MAGIC_NO_CHECK_APPTYPE  = 0x008000
    MAGIC_NO_CHECK_TOKENS   = 0x100000
    MAGIC_NO_CHECK_ENCODING = 0x200000

    MAGIC_FLAGS = MAGIC_NO_CHECK_TEXT | MAGIC_NO_CHECK_ENCODING | MAGIC_NO_CHECK_APPTYPE | MAGIC_NO_CHECK_TOKENS

    LIBRARY = "magic"

    def __init__(self, magic_file=None, flags=0, keep_going=False):
        if magic_file:
            self.magic_file = str2bytes(magic_file)
        else:
            self.magic_file = None

        if keep_going:
            flags = flags | self.MAGIC_CONTINUE

        self.libmagic = binwalk.core.C.Library(self.LIBRARY, self.LIBMAGIC_FUNCTIONS)

        binwalk.core.common.debug("libmagic.magic_open(0x%X)" % (self.MAGIC_FLAGS | flags))
        self.magic_cookie = self.libmagic.magic_open(self.MAGIC_FLAGS | flags)

        binwalk.core.common.debug("libmagic.magic_load(%s, %s)" % (type(self.magic_cookie), self.magic_file))
        self.libmagic.magic_load(self.magic_cookie, self.magic_file)
        binwalk.core.common.debug("libmagic loaded OK!")

    def close(self):
        if self.magic_cookie:
            self.libmagic.magic_close(self.magic_cookie)
            del self.magic_cookie
            self.magic_cookie = None

    def buffer(self, data):
        if self.magic_cookie:
            return self.libmagic.magic_buffer(self.magic_cookie, str2bytes(data), len(data))

