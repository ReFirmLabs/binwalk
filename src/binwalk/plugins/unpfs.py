import os
import errno
import struct
import binwalk.core.plugin
import binwalk.core.compat
from binwalk.core.common import BlockFile as open

class PFSCommon(object):

    def _make_short(self, data, endianess):
        """Returns a 2 byte integer."""
        data = binwalk.core.compat.str2bytes(data)
        return struct.unpack('%sH' % endianess, data)[0]

    def _make_int(self, data, endianess):
        """Returns a 4 byte integer."""
        data = binwalk.core.compat.str2bytes(data)
        return struct.unpack('%sI' % endianess, data)[0]

class PFS(PFSCommon):
    """Class for accessing PFS meta-data."""
    HEADER_SIZE = 16

    def __init__(self, fname, endianess='<'):
        self.endianess = endianess
        self.meta = open(fname, 'rb')
        header = self.meta.read(self.HEADER_SIZE)
        self.file_list_start = self.meta.tell()
        
        self.num_files = self._make_short(header[-2:], endianess)
        self.node_size = self._get_fname_len() + 12
    
    def _get_fname_len(self, bufflen=128):
        """Returns the number of bytes designated for the filename."""
        buff = self.meta.peek(bufflen)
        strlen = buff.find('\0')
        for i, b in enumerate(buff[strlen:]):
            if b != '\0':
                return strlen+i
        return bufflen
    
    def _get_node(self):
        """Reads a chunk of meta data from file and returns a PFSNode."""
        data = self.meta.read(self.node_size)
        return PFSNode(data, self.endianess)

    def get_end_of_meta_data(self):
        """Returns integer indicating the end of the file system meta data."""
        return self.HEADER_SIZE + self.node_size * self.num_files

    def entries(self):
        """Returns file meta-data entries one by one."""
        self.meta.seek(self.file_list_start)
        for i in range(0, self.num_files):
            yield self._get_node()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.meta.close()

class PFSNode(PFSCommon):
    """A node in the PFS Filesystem containing meta-data about a single file."""

    def __init__(self, data, endianess):
        self.fname, data = data[:-12], data[-12:]
        self._decode_fname()
        self.inode_no = self._make_int(data[:4], endianess)
        self.foffset = self._make_int(data[4:8], endianess)
        self.fsize = self._make_int(data[8:], endianess)

    def _decode_fname(self):
        """Extracts the actual string from the available bytes."""
        self.fname = self.fname[:self.fname.find('\0')]
        self.fname = self.fname.replace('\\', '/')

class PFSExtractor(binwalk.core.plugin.Plugin):
    """
    Extractor for known PFS/0.9 File System Formats.
    """
    MODULES = ['Signature']
    
    def init(self):
        if self.module.extractor.enabled:
            self.module.extractor.add_rule(regex='^pfs filesystem',
                                           extension='pfs',
                                           cmd=self.extractor)

    def _create_dir_from_fname(self, fname):
        try:
            os.makedirs(os.path.dirname(fname))
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise e

    def extractor(self, fname):
        fname = os.path.abspath(fname)
        try:
            with PFS(fname) as fs:
                # The end of PFS meta data is the start of the actual data
                data = open(fname, 'rb')
                data.seek(fs.get_end_of_meta_data())
                for entry in fs.entries():
                    self._create_dir_from_fname(entry.fname)
                    outfile = open(entry.fname, 'wb')
                    outfile.write(data.read(entry.fsize))
                    outfile.close()
                data.close()
        except KeyboardInterrupt as e:
            raise e
        except Exception as e:
            return False

        return True
