import os
import zlib
import struct
import binwalk.core.plugin
import binwalk.core.common
try:
    import lzma
except ImportError as e:
    pass


class RomFSCommon(object):

    def _read_next_word(self):
        value = struct.unpack("%sL" % self.endianness, self.data[self.index:self.index + 4])[0]
        self.index += 4
        return value

    def _read_next_uid(self):
        uid = int(self.data[self.index:self.index + 4])
        self.index += 4
        return uid

    def _read_next_block(self, size):
        size = int(size)
        data = self.data[self.index:self.index + size]
        self.index += size
        return data

    def _read_next_string(self):
        data = ""
        while True:
            byte = self.data[self.index]
            try:
                byte = chr(byte)
            except TypeError as e:
                pass

            if byte == "\x00":
                break
            else:
                data += byte
                self.index += 1
        return data


class RomFSEntry(RomFSCommon):

    DIR_STRUCT_MASK = 0x00000001
    DATA_MASK = 0x00000008
    COMPRESSED_MASK = 0x005B0000

    def __init__(self, data, endianness="<"):
        self.data = data
        self.endianness = endianness
        self.index = 0

        self.type = self._read_next_word()
        self.unknown2 = self._read_next_word()
        self.unknown3 = self._read_next_word()
        self.size = self._read_next_word()
        self.unknown4 = self._read_next_word()
        self.offset = self._read_next_word()
        self.unknown5 = self._read_next_word()
        self.uid = self._read_next_uid()


class RomFSDirStruct(RomFSCommon):

    SIZE = 0x20

    def __init__(self, data, endianness="<"):
        self.index = 0
        self.data = data
        self.endianness = endianness
        self.directory = False
        self.uid = None
        self.ls = []

        for (uid, entry) in self.next():
            if self.uid is None:
                self.uid = uid

            if entry in ['.', '..']:
                self.directory = True
                continue

            self.ls.append((uid, entry))

    def next(self):
        while self.index < len(self.data):
            uid = self._read_next_word()
            dont_care = self._read_next_word()
            entry = self._read_next_string()

            total_size = int(4 + 4 + len(entry))
            count = int(total_size / self.SIZE)
            if count == 0:
                mod = self.SIZE - total_size
            else:
                mod = self.SIZE - int(total_size - (count * self.SIZE))

            if mod > 0:
                remainder = self._read_next_block(mod)

            yield (uid, entry)


class FileContainer(object):

    def __init__(self):
        pass


class RomFS(object):

    SUPERBLOCK_SIZE = 0x20
    FILE_ENTRY_SIZE = 0x20

    def __init__(self, fname, endianness="<"):
        self.endianness = endianness
        self.data = open(fname, "rb").read()
        self.entries = self._process_all_entries()

    def get_data(self, uid):
        start = self.entries[uid].offset
        end = start + self.entries[uid].size

        data = self.data[start:end]

        try:
            data = lzma.decompress(data)
        except KeyboardInterrupt as e:
            raise e
        except Exception as e:
            try:
                data = zlib.decompress(data)
            except KeyboardInterrupt as e:
                raise e
            except Exception as e:
                pass

        return data

    def build_path(self, uid):
        path = self.entries[uid].name

        while uid != 0:
            uid = self.entries[uid].parent
            path = os.path.join(self.entries[uid].name, path)

        return path.replace("..", "")

    def _process_all_entries(self):
        entries = {}
        offset = self.SUPERBLOCK_SIZE

        while True:
            try:
                entry = RomFSEntry(self.data[offset:offset + self.FILE_ENTRY_SIZE], endianness=self.endianness)
            except ValueError as e:
                break

            if not entry.uid in entries:
                entries[entry.uid] = FileContainer()

            entries[entry.uid].offset = entry.offset
            entries[entry.uid].size = entry.size
            entries[entry.uid].type = entry.type
            if entry.uid == 0:
                entries[entry.uid].name = os.path.sep

            if entry.type & entry.DIR_STRUCT_MASK:
                entries[entry.uid].type = "directory"
                ds = RomFSDirStruct(self.data[entry.offset:entry.offset + entry.size], endianness=self.endianness)
                for (uid, name) in ds.ls:
                    if not uid in entries:
                        entries[uid] = FileContainer()
                    entries[uid].parent = ds.uid
                    entries[uid].name = name
            else:
                entries[entry.uid].type = "data"

            offset += self.FILE_ENTRY_SIZE

        return entries


if __name__ == '__main__':
    import sys

    try:
        infile = sys.argv[1]
        outdir = sys.argv[2]
    except IndexError as e:
        print ("Usage: %s <input file> <output directory>" % sys.argv[0])
        sys.exit(1)


class DlinkROMFSExtractPlugin(binwalk.core.plugin.Plugin):

    '''
    Gzip extractor plugin.
    '''
    MODULES = ['Signature']
    BLOCK_SIZE = 10 * 1024

    def init(self):
        # If the extractor is enabled for the module we're currently loaded
        # into, then register self.extractor as a D-Link ROMFS file system
        # extraction rule.
        if self.module.extractor.enabled:
            self.module.extractor.add_rule(txtrule=None,
                                           regex="^d-link romfs filesystem",
                                           extension="romfs",
                                           recurse=False,
                                           cmd=self.extractor)

    def extractor(self, fname):
        infile = os.path.abspath(fname)
        outdir = os.path.join(os.path.dirname(infile), "romfs-root")
        outdir = binwalk.core.common.unique_file_name(outdir)

        # TODO: Support big endian targets.
        fs = RomFS(infile)
        os.mkdir(outdir)

        for (uid, info) in fs.entries.items():
            if hasattr(info, 'name') and hasattr(info, 'parent'):
                path = fs.build_path(uid).strip(os.path.sep)
                fname = os.path.join(outdir, path)

                if info.type == "directory" and not os.path.exists(fname):
                    os.makedirs(fname)
                else:
                    fdata = fs.get_data(uid)
                    with open(fname, 'wb') as fp:
                        fp.write(fdata)

        return True
