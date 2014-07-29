# Special overrides/workarounds for running as an IDA plugin

import io
import os
import logging

class ShutUpHashlib(logging.Filter):
    '''
    This is used to suppress hashlib exception messages
    if using the Python interpreter bundled with IDA.
    '''
    def filter(self, record):
        return not record.getMessage().startswith("code for hash")

try:
    import idc
    import idaapi
    LOADED_IN_IDA = True
    logger = logging.getLogger() 
    logger.addFilter(ShutUpHashlib())
except ImportError:
    LOADED_IN_IDA = False

def start_address():
    return idaapi.get_first_seg().startEA

def end_address():
    last_ea = idc.BADADDR
    seg = idaapi.get_first_seg()

    while seg:
        last_ea = seg.endEA
        seg = idaapi.get_next_seg(last_ea)

    return last_ea

class IDBFileIO(io.FileIO):
    '''
    A custom class to override binwalk.core.common.Blockfile in order to
    read data directly out of the IDB, rather than reading from the original
    file on disk, which may or may not still exist.

    Requests to read from files that are not the current IDB are just forwarded
    up to io.FileIO.
    '''

    def __init__(self, fname, mode):
        if idc.GetIdbPath() != fname:
            self.__idb__ = False
            super(IDBFileIO, self).__init__(fname, mode)
        else:
            self.__idb__ = True
            self.name = fname
            self.idb_start = 0
            self.idb_pos = 0
            self.idb_end = end_address()

            if self.size == 0:
                self.size = end_address() - start_address()

            if self.length == 0:
                self.length = self.size

            if self.offset == 0:
                self.offset = start_address()

    def read(self, n=-1):
        if not self.__idb__:
            return super(IDBFileIO, self).read(n)
        else:
            data = ''
            start_n = n
            start_idb_pos = self.idb_pos

            while n and self.idb_pos <= self.idb_end:
                # This generally assumes 8-bit bytes
                data += chr(idc.Byte(self.idb_pos))
                self.idb_pos += 1
                n -= 1
            
            return data

    def write(self, data):
        if not self.__idb__:
            return super(IDBFileIO, self).write(data)
        else:
            # Don't actually write anything to the IDB, as, IMHO,
            # a binwalk plugin should never do this. But return the
            # number of bytes we were requested to write so that 
            # any callers are happy.
            return len(data)

    def seek(self, n, whence=os.SEEK_SET):
        if not self.__idb__:
            return super(IDBFileIO, self).seek(n, whence)
        else:
            if whence == os.SEEK_SET:
                self.idb_pos = self.idb_start + n
            elif whence == os.SEEK_CUR:
                self.idb_pos += n
            elif whence == os.SEEK_END:
                self.idb_pos = self.idb_end + n

    def tell(self):
        if not self.__idb__:
            return super(IDBFileIO, self).tell()
        else:
            return self.idb_pos

