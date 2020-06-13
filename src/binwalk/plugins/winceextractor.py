#! /usr/bin/env python3

"""

WinCE Extractor: Extract compressed files from Windows CE ROMs.

"""

from typing import IO, BinaryIO, Union
import ctypes
import os
import sys
import io
import argparse

from wincedecompr import CEDecompressROM

_IMGOFSINCREMENT = 0x1000
_IMAGE_DOS_SIGNATURE = 0x5A4D
_ROM_EXTRA = 9
_XIP_NAMELEN = 32
_PID_LENGTH = 10
_STD_EXTRA = 16
_E32OBJNAMEBYTES = 8
_IMAGE_FILE_RELOCS_STRIPPED = 0x0001
_IMAGE_SCN_CNT_CODE = 0x00000020
_IMAGE_SCN_CNT_INITIALIZED_DATA = 0x00000040
_IMAGE_SCN_CNT_UNINITIALIZED_DATA = 0x00000080
_IMAGE_SCN_COMPRESSED = 0x00002000
_ROM_SIGNATURE_OFFSET = 64
_ROM_SIGNATURE = 0x43454345
_MAX_ROM = 32
_EXP = 0
_IMP = 1
_RES = 2
_EXC = 3
_SEC = 4
_FIX = 5
_DEB = 6
_IMD = 7
_MSP = 8
_TLS = 9
_CBK = 10
_RS1 = 11
_RS2 = 12
_RS3 = 13
_RS4 = 14
_RS5 = 15

_ST_TEXT = 0
_ST_DATA = 1
_ST_PDATA = 2
_ST_RSRC = 3
_ST_OTHER = 4

_CECOMPRESS_ALLZEROS = 0
_CECOMPRESS_FAILED = 0xffffffff
_CEDECOMPRESS_FAILED = 0xffffffff


class FileType(object):
    """
    An enum-like class denoting a ROM's file type.
    """
    FT_BOOOFF = 0
    FT_NBF = 1
    FT_BIN = 2


class FileTime(ctypes.Structure):
    """
    A structure for holding a filetime instance in a ROM entry.
    """
    _fields_ = [("dwLowDateTime", ctypes.c_uint32),
                ("dwHighDateTime", ctypes.c_uint32)]


class Info(ctypes.Structure):
    """
    A structure for holding information about units
    in other structures.
    """
    _fields_ = [("rva", ctypes.c_uint32),
                ("size", ctypes.c_uint32)]


class e32_rom(ctypes.Structure):
    """
    A structure representing an e32_rom entry.
    """
    _fields_ = [("e32_objcnt", ctypes.c_uint16),
                ("e32_imageflags", ctypes.c_uint16),
                ("e32_entryrva", ctypes.c_uint32),
                ("e32_vbase", ctypes.c_uint32),
                ("e32_subsysmajor", ctypes.c_uint16),
                ("e32_subsysminor", ctypes.c_uint16),
                ("e32_stackmax", ctypes.c_uint32),
                ("e32_vsize", ctypes.c_uint32),
                ("e32_sect14rva", ctypes.c_uint32),
                ("e32_sect14size", ctypes.c_uint32),
                ("e32_unit", Info * _ROM_EXTRA),
                ("e32_subsys", ctypes.c_uint16)]


class o32_rom(ctypes.Structure):
    """
    A structure representing an o32_rom entry.
    """
    _fields_ = [("o32_vsize", ctypes.c_uint32),
                ("o32_rva", ctypes.c_uint32),
                ("o32_psize", ctypes.c_uint32),
                ("o32_dataptr", ctypes.c_uint32),
                ("o32_realaddr", ctypes.c_uint32),
                ("o32_flags", ctypes.c_uint32)]


class RomHdr(ctypes.Structure):
    """
    A structure representing a romhdr entry.
    """
    _fields_ = [("dllfirst", ctypes.c_uint32),
                ("dlllast", ctypes.c_uint32),
                ("physfirst", ctypes.c_uint32),
                ("physlast", ctypes.c_uint32),
                ("nummods", ctypes.c_uint32),
                ("ulRAMStart", ctypes.c_uint32),
                ("ulRAMFree", ctypes.c_uint32),
                ("ulRAMEnd", ctypes.c_uint32),
                ("ulCopyEntries", ctypes.c_uint32),
                ("ulCopyOffset", ctypes.c_uint32),
                ("ulProfileLen", ctypes.c_uint32),
                ("ulProfileOffset", ctypes.c_uint32),
                ("numfiles", ctypes.c_uint32),
                ("ulKernelFlags", ctypes.c_uint32),
                ("ulFSRamPercent", ctypes.c_uint32),
                ("ulDrivglobstart", ctypes.c_uint32),
                ("ulDrivgloblen", ctypes.c_uint32),
                ("usCPUType", ctypes.c_uint16),
                ("usMiscFlags", ctypes.c_uint16),
                ("pExtensions", ctypes.c_uint32),  # Originally void*, but Python makes pointers 8 bytes
                # and it needs to be a 4 byte pointer.
                ("ulTrackingStart", ctypes.c_uint32),
                ("ulTrackingLen", ctypes.c_uint32)]


class TocEntry(ctypes.Structure):
    """
    A structure representing a TOC entry.
    """
    _fields_ = [("dwFileAttributes", ctypes.c_uint32),
                ("ftTime", FileTime),
                ("nFileSize", ctypes.c_uint32),
                ("lpszFileName", ctypes.c_uint32),  # Originally void*, but Python makes pointers 8 bytes
                # and it needs to be a 4 byte pointer.
                ("ulE32Offset", ctypes.c_uint32),
                ("ulO32Offset", ctypes.c_uint32),
                ("ulLoadOffset", ctypes.c_uint32)]


class FileEntry(ctypes.Structure):
    """
    A structure representing a file entry.
    """
    _fields_ = [("dwFileAttributes", ctypes.c_uint32),
                ("ftTime", FileTime),
                ("nRealFileSize", ctypes.c_uint32),
                ("nCompFileSize", ctypes.c_uint32),
                ("lpszFileName", ctypes.c_uint32),  # Originally void*, but Python makes pointers 8 bytes
                # and it needs to be a 4 byte pointer.
                ("ulLoadOffset", ctypes.c_uint32)]


class CopyEntry(ctypes.Structure):
    """
    A structure representing a copy entry.
    """
    _fields_ = [("ulSource", ctypes.c_uint32),
                ("ulDest", ctypes.c_uint32),
                ("ulCopyLen", ctypes.c_uint32),
                ("ulDestLen", ctypes.c_uint32)]


class XipChainEntry(ctypes.Structure):
    """
    A structure representing a xipchain entry.
    """
    _fields_ = [("pvAddr", ctypes.c_void_p),
                ("dwLength", ctypes.c_uint32),
                ("dwMaxLength", ctypes.c_uint32),
                ("usOrder", ctypes.c_uint16),
                ("usFlags", ctypes.c_uint16),
                ("dwVersion", ctypes.c_uint32),
                ("szName", ctypes.c_char * _XIP_NAMELEN),
                ("dwAlgoFlags", ctypes.c_uint32),
                ("dwKeyLen", ctypes.c_uint32),
                ("byPublicKey", ctypes.c_ubyte * 596)]


class XipChainInfo(ctypes.Structure):
    """
    A structure holding information about a xipchain entry.
    """
    _fields_ = [("cXIPs", ctypes.c_uint32),
                ("xipEntryStart", XipChainEntry)]


class RomPid(ctypes.Structure):
    """
    A structure for holding information about extension entries.
    """

    class _RomPidAnonUnion(ctypes.Union):
        """
        Information about a rom pid sharing space with an array of DWORDs.
        """

        class _RomPidUnionStruct(ctypes.Structure):
            """
            Information about a rom pid.
            """
            _fields_ = [("name", ctypes.c_char * (_PID_LENGTH - 4) * ctypes.sizeof(ctypes.c_uint32)),
                        ("type", ctypes.c_uint32),
                        ("pdata", ctypes.c_uint32),
                        #    ("pdata",    ctypes.c_void_p),
                        ("length", ctypes.c_uint32),
                        ("reserved", ctypes.c_uint32)]

        _fields_ = [("dwPID", ctypes.c_uint32 * _PID_LENGTH),
                    ("s", _RomPidUnionStruct)]

    _anonymous_ = 'u'
    _fields_ = [('u', _RomPidAnonUnion),
                ('pNextExt', ctypes.c_uint32)]
    #    ('pNextExt', ctypes.c_void_p)]


class ImageDosHeader(ctypes.Structure):
    """
    A structure representing the header of DOS images.
    """
    _fields_ = [("e_magic", ctypes.c_uint16),
                ("e_cblp", ctypes.c_uint16),
                ("e_cp", ctypes.c_uint16),
                ("e_crlc", ctypes.c_uint16),
                ("e_cparhdr", ctypes.c_uint16),
                ("e_minalloc", ctypes.c_uint16),
                ("e_maxalloc", ctypes.c_uint16),
                ("e_ss", ctypes.c_uint16),
                ("e_sp", ctypes.c_uint16),
                ("e_csum", ctypes.c_uint16),
                ("e_ip", ctypes.c_uint16),
                ("e_cs", ctypes.c_uint16),
                ("e_lfarlc", ctypes.c_uint16),
                ("e_ovno", ctypes.c_uint16),
                ("e_res", ctypes.c_uint16 * 4),
                ("e_oemid", ctypes.c_uint16),
                ("e_oeminfo", ctypes.c_uint16),
                ("e_res2", ctypes.c_uint16 * 10),
                ("e_lfanew", ctypes.c_int32)]


class e32_exe(ctypes.Structure):
    """
    A structure representing a e32_exe entry.
    """
    _fields_ = [("e32_magic", ctypes.c_ubyte * 4),
                ("e32_cpu", ctypes.c_uint16),
                ("e32_objcnt", ctypes.c_uint16),
                ("e32_timestamp", ctypes.c_uint32),
                ("e32_symtaboff", ctypes.c_uint32),
                ("e32_symcount", ctypes.c_uint32),
                ("e32_opthdrsize", ctypes.c_uint16),
                ("e32_imageflags", ctypes.c_uint16),
                ("e32_coffmagic", ctypes.c_uint16),
                ("e32_linkmajor", ctypes.c_ubyte),
                ("e32_linkminor", ctypes.c_ubyte),
                ("e32_codesize", ctypes.c_uint32),
                ("e32_initdsize", ctypes.c_uint32),
                ("e32_uninitdsize", ctypes.c_uint32),
                ("e32_entryrva", ctypes.c_uint32),
                ("e32_codebase", ctypes.c_uint32),
                ("e32_database", ctypes.c_uint32),
                ("e32_vbase", ctypes.c_uint32),
                ("e32_objalign", ctypes.c_uint32),
                ("e32_filealign", ctypes.c_uint32),
                ("e32_osmajor", ctypes.c_uint16),
                ("e32_osminor", ctypes.c_uint16),
                ("e32_usermajor", ctypes.c_uint16),
                ("e32_userminor", ctypes.c_uint16),
                ("e32_subsysmajor", ctypes.c_uint16),
                ("e32_subsysminor", ctypes.c_uint16),
                ("e32_res1", ctypes.c_uint32),
                ("e32_vsize", ctypes.c_uint32),
                ("e32_hdrsize", ctypes.c_uint32),
                ("e32_filechksum", ctypes.c_uint32),
                ("e32_subsys", ctypes.c_uint16),
                ("e32_dllflags", ctypes.c_uint16),
                ("e32_stackmax", ctypes.c_uint32),
                ("e32_stackinit", ctypes.c_uint32),
                ("e32_heapmax", ctypes.c_uint32),
                ("e32_heapinit", ctypes.c_uint32),
                ("e32_res2", ctypes.c_uint32),
                ("e32_hdrextra", ctypes.c_uint32),
                ("e32_unit", Info * _STD_EXTRA)]


class o32_obj(ctypes.Structure):
    """
    A structure for representing an o32_obj entry.
    """
    _fields_ = [("o32_name", ctypes.c_ubyte * _E32OBJNAMEBYTES),
                ("o32_vsize", ctypes.c_uint32),
                ("o32_rva", ctypes.c_uint32),
                ("o32_psize", ctypes.c_uint32),
                ("o32_dataptr", ctypes.c_uint32),
                ("o32_realaddr", ctypes.c_uint32),
                ("o32_access", ctypes.c_uint32),
                ("o32_temp3", ctypes.c_uint32),
                ("o32_flags", ctypes.c_uint32)]


class B000FFHeader(ctypes.Structure):
    """
    A structure holding the header of a B000FF file.
    """
    _fields_ = [("signature", ctypes.c_char * 7),
                ("imgstart", ctypes.c_uint32),
                ("imglength", ctypes.c_uint32),
                ("blockstart", ctypes.c_uint32),
                ("blocklength", ctypes.c_uint32),
                ("blockchecksum", ctypes.c_uint32),
                ("data", ctypes.c_ubyte * 1)]


def write_blanks(f: IO, n_blanks: int) -> None:
    """
    Extends the current file by n_blanks amount of bytes from the current position.

    :param f: file to extend
    :param n_blanks: number of bytes to extend by

    :return: None
    """
    f.seek(n_blanks, io.SEEK_CUR)


def write_alignment(f: IO, page_size: int) -> None:
    """
    Writes blanks to the given file to fill the current page size gap.

    :param f: file to write to
    :param page_size: a page size

    :return: None
    """
    cur_ofs = f.tell()
    if cur_ofs % page_size != 0:
        write_blanks(f, page_size - (cur_ofs % page_size))


def write_dummy_mz_header(f: BinaryIO) -> None:
    """
    Writes a image DOS header to the given file.

    :param f: file to write to

    :return: None
    """
    dos = ImageDosHeader()

    dos.e_magic = _IMAGE_DOS_SIGNATURE
    dos.e_cblp = 0x90
    dos.e_cp = 3
    dos.e_cparhdr = 0x4
    dos.e_maxalloc = 0xffff
    dos.e_sp = 0xb8
    dos.e_lfarlc = 0x40
    dos.e_lfanew = 0xc0

    doscode = bytes([0x0e, 0x1f, 0xba, 0x0e, 0x00, 0xb4, 0x09, 0xcd, 0x21, 0xb8, 0x01, 0x4c, 0xcd, 0x21, 0x54, 0x68,
                     0x69, 0x73, 0x20, 0x70, 0x72, 0x6f, 0x67, 0x72, 0x61, 0x6d, 0x20, 0x63, 0x61, 0x6e, 0x6e, 0x6f,
                     0x74, 0x20, 0x62, 0x65, 0x20, 0x72, 0x75, 0x6e, 0x20, 0x69, 0x6e, 0x20, 0x44, 0x4f, 0x53, 0x20,
                     0x6d, 0x6f, 0x64, 0x65, 0x2e, 0x0d, 0x0d, 0x0a, 0x24, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

    f.write(dos)
    f.write(doscode)
    write_blanks(f, 0x40)


def filetime_to_time_t(pft: FileTime) -> int:
    """
    Converts a filetime structure to a time_t value.

    :param pft: a filetime structure
    
    :return: a time_t value
    """
    t = pft.dwHighDateTime
    t <<= 32
    t |= pft.dwLowDateTime
    t //= 10000000
    t -= 11644473600

    return t


def read_dword(data: bytes, offset: int, byteorder: str) -> int:
    """
    Reads a ctypes.c_uint32 integer from the given data at the given offset.

    :param data: input data
    :param offset: offset to starting reading
    :param byteorder: order to read the bytes in

    :return: a ctypes.c_uint32 integer
    """
    return int.from_bytes(data[offset:offset + ctypes.sizeof(ctypes.c_uint32)], byteorder=byteorder)


def load_from_offset(data: bytes, offset: int, structure: ctypes.Structure) -> ctypes.Structure:
    """
    Loads information from the given sequence of bytes and offset into a specified
    structure type.

    :param data: input data
    :param offset: offset to start reading
    :param structure: the type of structure to create and fill

    :return: a structure that is to be filled from the bytes at the given offset
    """
    return structure.from_buffer_copy(data[offset:offset + ctypes.sizeof(structure)])


def set_to_image_start(in_f: BinaryIO, byteorder: str) -> bool:
    """
    Moves the given file's position to the start of a Win CE ROM file.

    :param in_f: input file
    :param byteorder: byte ordering to read in values

    :return: None
    """
    while True:
        n = in_f.read(ctypes.sizeof(ctypes.c_uint32))
        if len(n) != ctypes.sizeof(ctypes.c_uint32):
            return False
        offset = int.from_bytes(n, byteorder=byteorder)
        if offset == _ROM_SIGNATURE:
            in_f.seek(-_ROM_SIGNATURE_OFFSET - 4, io.SEEK_CUR)
            return True
        in_f.seek(-1, io.SEEK_CUR)


def read_null_terminated_string(data: bytes, offset: int, encoding: str = 'ascii') -> str:
    """
    Returns a null terminated string starting from the given offset
    into the given data.

    :param data: a continous sequence of bytes
    :param offset: offset to start looking
    :param encoding: an encoding to interpret the string

    :return: the found string
    """
    start = offset
    current = offset
    while data[current] != 0:
        current += 1

    return data[start:current].decode(encoding)


class DecompressionFailedException(Exception):
    def __init__(self):
        super().__init__()


class WinCEExtractor(object):
    """
    Extracts information and files from a Windows CE ROM file.
    """

    def __init__(self, file_obj: BinaryIO, image_start: int = None):
        self.romhdr_offset = 0
        self.load_offset = 0
        self.in_file = file_obj

        if image_start is None:
            set_to_image_start(file_obj, byteorder='little')
        else:
            file_obj.seek(image_start, io.SEEK_CUR)

        self.data = None
        self.modules = []
        self.files = []

    def __enter__(self):
        self.analyze()
        return self

    def __exit__(self, type_, value, traceback):
        del self.data
        del self.modules
        del self.files

    def analyze(self) -> None:
        """
        Starts analysis on the ROM file. Collects modules and files.

        :return: None
        """
        self.data = self.in_file.read()
        self.modules.clear()
        self.files.clear()

        self.romhdr_offset = read_dword(self.data, _ROM_SIGNATURE_OFFSET + 8, byteorder='little')
        self.load_offset = read_dword(self.data, _ROM_SIGNATURE_OFFSET + 4, byteorder='little') - self.romhdr_offset

        romhdr_s = load_from_offset(self.data, self.romhdr_offset, RomHdr)

        for i in range(romhdr_s.nummods):
            toc_s = load_from_offset(self.data,
                                     self.romhdr_offset + ctypes.sizeof(RomHdr) + (ctypes.sizeof(TocEntry) * i),
                                     TocEntry)
            self.modules.append(WinModule(self, toc_s, romhdr_s))

        toc_f_offset = self.romhdr_offset + ctypes.sizeof(RomHdr) + (ctypes.sizeof(TocEntry) * romhdr_s.nummods)

        for i in range(romhdr_s.numfiles):
            toc_f_s = load_from_offset(self.data, toc_f_offset + (ctypes.sizeof(FileEntry) * i), FileEntry)
            self.files.append(WinFile(self, toc_f_s))

    def minus_load_offset(self, offset: int) -> int:
        """
        Gives back an offset that was subtracted by the currently
        known loading offset.

        :param offset: a given offset

        :return: the given offset subtracted by a known load offset
        """
        return offset - self.load_offset

    def extract_data(self, out_f: BinaryIO, offset: int, datasize: int, is_compressed: bool,
                     max_uncompressed_size: int) -> int:
        """
        Uses the CEDecompressROM Windows decompression algorithm to decompress the ROM data and write out its files.

        :param out_f: file to write to
        :param offset: the beginning of the o32_rom object
        :param datasize: size of the o32_rom object
        :param is_compressed: whether the contents are compressed and need to be decompressed first
        :param max_uncompressed_size: the amount of data to uncompress

        :return: how many bytes were written
        """
        buf = memoryview(self.data)[offset:offset + datasize]

        buf_len = datasize
        if datasize != max_uncompressed_size and is_compressed:
            decompressed_buf = bytearray(max_uncompressed_size + 4096)
            buf_len = CEDecompressROM(buf, datasize, decompressed_buf, max_uncompressed_size, 0, 1, 4096)

            if buf_len != _CEDECOMPRESS_FAILED:
                buf = decompressed_buf
            else:
                raise DecompressionFailedException()

        return out_f.write(buf[:buf_len])


class WinEntry(object):
    """
    A class holding either a toc_entry or a file_entry and ability to write out their contents to a file.
    """

    def __init__(self, extractor: WinCEExtractor, entry: Union[TocEntry, FileEntry]):
        self.extractor = extractor
        self.entry = entry
        self.file_name = read_null_terminated_string(self.extractor.data,
                                                     self.extractor.minus_load_offset(self.entry.lpszFileName))

    def write_to(self, out_f: BinaryIO) -> None:
        """
        Writes out the contents of the current entry to the given file.

        :param out_f: file to write to

        :return: None
        """
        raise NotImplementedError()


class WinFile(WinEntry):
    def __init__(self, extractor: WinCEExtractor, entry: FileEntry):
        super().__init__(extractor, entry)

    def write_to(self, out_f: BinaryIO) -> None:
        """
        Writes out the contents of the current entry to the given file.

        :param out_f: file to write to

        :return: None
        """
        self.extractor.extract_data(out_f, self.extractor.minus_load_offset(self.entry.ulLoadOffset),
                                    self.entry.nCompFileSize, self.entry.nCompFileSize != self.entry.nRealFileSize,
                                    self.entry.nRealFileSize)


class WinModule(WinEntry):
    SEGMENT_NAMES = [".text", ".data", ".pdata", ".rsrc", ".other"]

    def __init__(self, extractor: WinCEExtractor, toc: TocEntry, rom: RomHdr):
        super().__init__(extractor, toc)

        self.__segment_name_usage = [0, 0, 0, 0, 0]
        self.rom = rom
        self.e32 = load_from_offset(self.extractor.data, self.extractor.minus_load_offset(toc.ulE32Offset), e32_rom)
        self.o32_offset = self.extractor.minus_load_offset(toc.ulO32Offset)

        self.o32_roms = []

        for i in range(self.e32.e32_objcnt):
            self.o32_roms.append(
                load_from_offset(self.extractor.data, self.o32_offset + (ctypes.sizeof(o32_rom) * i), o32_rom))

    def write_to(self, out_f: BinaryIO) -> None:
        """
        Writes out the contents of the current entry to the given file.

        :param out_f: file to write to

        :return: None
        """
        write_dummy_mz_header(out_f)
        e32_ofs = out_f.tell()
        self.__write_e32_header(out_f)

        o32_ofs_list = []
        data_ofs_list = []
        data_len_list = []

        for o32_s in self.o32_roms:
            o32_ofs_list.append(out_f.tell())
            self.__write_o32_header(out_f, o32_s)

        write_alignment(out_f, 0x200)
        header_size = out_f.tell()

        for o32_s in self.o32_roms:
            data_ofs_list.append(out_f.tell())

            data_len = self.extractor.extract_data(out_f, self.extractor.minus_load_offset(o32_s.o32_dataptr),
                                                   min(o32_s.o32_vsize, o32_s.o32_psize),
                                                   (o32_s.o32_flags & _IMAGE_SCN_COMPRESSED) != 0, o32_s.o32_vsize)

            data_len_list.append(data_len)
            write_alignment(out_f, 0x200)

        total_file_size = out_f.tell()

        for i, _ in enumerate(self.o32_roms):
            out_f.seek(o32_ofs_list[i] + 16, io.SEEK_SET)
            out_f.write(data_len_list[i].to_bytes(ctypes.sizeof(ctypes.c_uint32), byteorder=sys.byteorder))
            out_f.write(data_ofs_list[i].to_bytes(ctypes.sizeof(ctypes.c_uint32), byteorder=sys.byteorder))

            out_f.seek(e32_ofs + 0x54, io.SEEK_SET)  # ofs to e32_hdrsize
            out_f.write(header_size.to_bytes(ctypes.sizeof(ctypes.c_uint32), byteorder=sys.byteorder))
            out_f.seek(total_file_size, io.SEEK_SET)

    def __write_e32_header(self, out_f: BinaryIO) -> None:
        """
        Writes an e32 object to the file.

        :param out_f: file to write to

        :return: None
        """
        pe32 = e32_exe()

        pe32.e32_magic[0] = ord('P')
        pe32.e32_magic[1] = ord('E')
        pe32.e32_cpu = self.rom.usCPUType
        pe32.e32_objcnt = self.e32.e32_objcnt
        pe32.e32_timestamp = filetime_to_time_t(self.entry.ftTime)
        pe32.e32_symtaboff = 0
        pe32.e32_symcount = 0
        pe32.e32_opthdrsize = 0xe0
        pe32.e32_imageflags = self.e32.e32_imageflags | _IMAGE_FILE_RELOCS_STRIPPED
        pe32.e32_coffmagic = 0x10b
        pe32.e32_linkmajor = 6
        pe32.e32_linkminor = 1
        pe32.e32_codesize = self.__calculate_segment_size_sum(_IMAGE_SCN_CNT_CODE)
        pe32.e32_initdsize = self.__calculate_segment_size_sum(_IMAGE_SCN_CNT_INITIALIZED_DATA)
        pe32.e32_uninitdsize = self.__calculate_segment_size_sum(_IMAGE_SCN_CNT_UNINITIALIZED_DATA)
        pe32.e32_entryrva = self.e32.e32_entryrva
        pe32.e32_codebase = self.__find_first_segment(_IMAGE_SCN_CNT_CODE)
        pe32.e32_database = self.__find_first_segment(_IMAGE_SCN_CNT_INITIALIZED_DATA)
        pe32.e32_vbase = self.e32.e32_vbase
        pe32.e32_objalign = 0x1000
        pe32.e32_filealign = 0x200
        pe32.e32_osmajor = 4
        pe32.e32_osminor = 0
        pe32.e32_subsysmajor = self.e32.e32_subsysmajor
        pe32.e32_subsysminor = self.e32.e32_subsysminor
        pe32.e32_vsize = self.e32.e32_vsize
        pe32.e32_filechksum = 0
        pe32.e32_subsys = self.e32.e32_subsys
        pe32.e32_stackmax = self.e32.e32_stackmax
        pe32.e32_stackinit = 0x1000
        pe32.e32_heapmax = 0x100000
        pe32.e32_heapinit = 0x1000
        pe32.e32_hdrextra = _STD_EXTRA

        pe32.e32_unit[_EXP] = self.e32.e32_unit[_EXP]
        pe32.e32_unit[_IMP] = self.e32.e32_unit[_IMP]
        pe32.e32_unit[_RES] = self.e32.e32_unit[_RES]
        pe32.e32_unit[_EXC] = self.e32.e32_unit[_EXC]
        pe32.e32_unit[_SEC] = self.e32.e32_unit[_SEC]
        pe32.e32_unit[_IMD] = self.e32.e32_unit[_IMD]
        pe32.e32_unit[_MSP] = self.e32.e32_unit[_MSP]
        pe32.e32_unit[_RS4].rva = self.e32.e32_sect14rva
        pe32.e32_unit[_RS4].size = self.e32.e32_sect14size

        out_f.write(pe32)

    def __write_o32_header(self, out_f: BinaryIO, o32: o32_rom) -> None:
        """
        Writes an o32 object to the file.

        :param out_f: file to write to
        :param o32: o32_rom structure

        :return: None
        """
        po32 = o32_obj()

        if self.e32.e32_unit[_RES].rva == o32.o32_rva and self.e32.e32_units[_RES].size == o32.o32_vsize:
            seg_type = _ST_RSRC
        elif self.e32.e32_unit[_EXC].rva == o32.o32_rva and self.e32.e32_unit[_EXC].size == o32.o32_vsize:
            seg_type = _ST_PDATA
        elif (o32.o32_flags & _IMAGE_SCN_CNT_CODE) != 0:
            seg_type = _ST_TEXT
        elif (o32.o32_flags & _IMAGE_SCN_CNT_INITIALIZED_DATA) != 0:
            seg_type = _ST_DATA
        elif (o32.o32_flags & _IMAGE_SCN_CNT_UNINITIALIZED_DATA) != 0:
            seg_type = _ST_PDATA
        else:
            seg_type = _ST_OTHER

        segment_name = WinModule.SEGMENT_NAMES[seg_type]
        if self.__segment_name_usage[seg_type] != 0:
            segment_name += str(self.__segment_name_usage[seg_type])

        po32.o32_name[:] = segment_name.encode('ascii')[:_E32OBJNAMEBYTES].ljust(_E32OBJNAMEBYTES, '\0'.encode('ascii'))

        self.__segment_name_usage[seg_type] += 1

        po32.o32_vsize = o32.o32_vsize
        po32.o32_rva = o32.o32_realaddr - self.e32.e32_vbase
        po32.o32_psize = 0
        po32.o32_dataptr = 0
        po32.o32_realaddr = 0
        po32.o32_access = 0
        po32.o32_temp3 = 0
        po32.o32_flags = o32.o32_flags & (~_IMAGE_SCN_COMPRESSED)

        out_f.write(po32)

    def __calculate_segment_size_sum(self, segtype_flag: int) -> int:
        """
        Sums up all the o32 objects' vsize that match the segment type flags.

        :param segtype_flag: a flag of some sort

        :return: sum of vsizes
        """
        return sum(o32_s.o32_vsize for o32_s in self.o32_roms if (o32_s.o32_flags & segtype_flag) != 0)

    def __find_first_segment(self, segtype_flag: int) -> int:
        """
        Finds the first o32 that matches the given segment type flags.

        :param segtype_flag: the current flags to check

        :return: The o32 rva of the o32 object that matches the given flag, otherwise 0
        """
        for o32_s in self.o32_roms:
            if (o32_s.o32_flags & segtype_flag) != 0:
                return o32_s.o32_rva

        return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', metavar='dirpath', help='save found files/modules to this path')
    parser.add_argument('-o', metavar='offset', type=int, help='offset of the image file')
    parser.add_argument('image_file', help='ROM image to extract')

    args = parser.parse_args()

    image_file = args.image_file
    output_dir = args.d
    image_offset = args.o

    if not os.path.isfile(image_file):
        print(f'Cannot find file: {image_file}', file=sys.stderr)
        exit(1)

    if output_dir is not None:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        elif not os.path.isdir(output_dir):
            print(f'{output_dir} is not a valid directory', file=sys.stderr)
            exit(1)

    if image_offset is not None and image_offset < 0:
        print(f'Image offset cannot be less than 0', file=sys.stderr)

    with open(image_file, 'r+b') as f:
        with WinCEExtractor(f, image_offset) as extractor:
            if output_dir is not None:
                for module in extractor.modules:
                    with open(os.path.join(output_dir, module.file_name), 'w+b') as module_file:
                        try:
                            module.write_to(module_file)
                        except DecompressionFailedException:
                            print(f'Error decompressing file: {module.file_name}', file=sys.stderr)
                for file_e in extractor.files:
                    with open(os.path.join(output_dir, file_e.file_name), 'w+b') as file_file:
                        try:
                            file_e.write_to(file_file)
                        except DecompressionFailedException:
                            print(f'Error decompressing file: {file_e.file_name}', file=sys.stderr)

    if output_dir is not None:
        print(f'File extraction complete. Please check your output directory: {output_dir}')
