# NOTE: CECompress.dll and 32-bit Python are required to run this plugin.

import binwalk.core.plugin
import re
import os
import ctypes
import sys
import io
import signal
import platform
from ctypes import cdll

if os.name == 'nt':
    from ctypes import wintypes
    from ctypes.wintypes import WORD
    from ctypes.wintypes import DWORD
    from ctypes.wintypes import LONG
    from ctypes.wintypes import ULONG
    from ctypes.wintypes import USHORT
else:
    WORD    = ctypes.c_ushort
    DWORD   = ctypes.c_ulong
    LONG    = ctypes.c_long
    ULONG   = ctypes.c_ulong
    USHORT  = ctypes.c_ushort

_IMGOFSINCREMENT                    = 0x1000
_IMAGE_DOS_SIGNATURE                = 0x5A4D
_ROM_EXTRA                          = 9
_STD_EXTRA                          = 16
_E32OBJNAMEBYTES                    = 8
_SIGNATURE_OFFSET                   = 64
_IMAGE_FILE_RELOCS_STRIPPED         = 0x0001
_IMAGE_SCN_CNT_CODE                 = 0x00000020
_IMAGE_SCN_CNT_INITIALIZED_DATA     = 0x00000040
_IMAGE_SCN_CNT_UNINITIALIZED_DATA   = 0x00000080
_IMAGE_SCN_COMPRESSED               = 0x00002000
_EXP = 0
_IMP = 1
_RES = 2
_EXC = 3
_SEC = 4
_IMD = 7
_MSP = 8
_RS3 = 13
_RS4 = 14

_ST_TEXT    = 0
_ST_DATA    = 1
_ST_PDATA   = 2
_ST_RSRC    = 3
_ST_OTHER   = 4

_CEDECOMPRESS_FAILED = 0xffffffff

class filetime(ctypes.Structure):
    """
    A structure for holding a filetime instance in a ROM entry.
    """
    _fields_        = [("dwLowDateTime",    DWORD),
                       ("dwHighDateTime",   DWORD)]

class info(ctypes.Structure):
    """
    A structure for holding information about units
    in other structures.
    """
    _fields_        = [("rva",  ctypes.c_ulong),
                       ("size", ctypes.c_ulong)]

class romhdr(ctypes.Structure):
    """
    A structure representing a romhdr entry.
    """
    _fields_    = [("dllfirst",         ULONG),
                   ("dlllast",          ULONG),
                   ("physfirst",        ULONG),
                   ("physlast",         ULONG),
                   ("nummods",          ULONG),
                   ("ulRAMStart",       ULONG),
                   ("ulRAMFree",        ULONG),
                   ("ulRAMEnd",         ULONG),
                   ("ulCopyEntries",    ULONG),
                   ("ulCopyOffset",     ULONG),
                   ("ulProfileLen",     ULONG),
                   ("ulProfileOffset",  ULONG),
                   ("numfiles",         ULONG),
                   ("ulKernelFlags",    ULONG),
                   ("ulFSRamPercent",   ULONG),
                   ("ulDrivglobstart",  ULONG),
                   ("ulDrivgloblen",    ULONG),
                   ("usCPUType",        USHORT),
                   ("usMiscFlags",      USHORT),
                   ("pExtensions",      DWORD),
                   ("ulTrackingStart",  ULONG),
                   ("ulTrackingLen",    ULONG)]

class toc_entry(ctypes.Structure):
    """
    A structure representing a TOC entry.
    """
    _fields_    = [("dwFileAttributes", DWORD),
                    ("ftTime",          filetime),
                    ("nFileSize",       DWORD),
                    ("lpszFileName",    DWORD),
                    ("ulE32Offset",     ULONG),
                    ("ulO32Offset",     ULONG),
                    ("ulLoadOffset",    ULONG)]

class e32_rom(ctypes.Structure):
    """
    A structure representing an e32_rom entry.
    """
    _fields_    = [("e32_objcnt",       ctypes.c_ushort),
                   ("e32_imageflags",   ctypes.c_ushort),
                   ("e32_entryrva",     ctypes.c_ulong),
                   ("e32_vbase",        ctypes.c_ulong),
                   ("e32_subsysmajor",  ctypes.c_ushort),
                   ("e32_subsysminor",  ctypes.c_ushort),
                   ("e32_stackmax",     ctypes.c_ulong),
                   ("e32_vsize",        ctypes.c_ulong),
                   ("e32_sect14rva",    ctypes.c_ulong),
                   ("e32_sect14size",   ctypes.c_ulong),
                   ("e32_unit",         info * _ROM_EXTRA),
                   ("e32_subsys",       ctypes.c_ushort)]                    

class o32_rom(ctypes.Structure):
    """
    A structure representing an o32_rom entry.
    """
    _fields_    = [("o32_vsize",    ctypes.c_ulong),
                   ("o32_rva",      ctypes.c_ulong),
                   ("o32_psize",    ctypes.c_ulong),
                   ("o32_dataptr",  ctypes.c_ulong),
                   ("o32_realaddr", ctypes.c_ulong),
                   ("o32_flags",    ctypes.c_ulong)]

class image_dos_header(ctypes.Structure):
    """
    A structure representing the header of DOS images.
    """
    _fields_    = [("e_magic",      WORD),
                   ("e_cblp",       WORD),
                   ("e_cp",         WORD),
                   ("e_crlc",       WORD),
                   ("e_cparhdr",    WORD),
                   ("e_minalloc",   WORD),
                   ("e_maxalloc",   WORD),
                   ("e_ss",         WORD),
                   ("e_sp",         WORD),
                   ("e_csum",       WORD),
                   ("e_ip",         WORD),
                   ("e_cs",         WORD),
                   ("e_lfarlc",     WORD),
                   ("e_ovno",       WORD),
                   ("e_res",        WORD * 4),
                   ("e_oemid",      WORD),
                   ("e_oeminfo",    WORD),
                   ("e_res2",       WORD * 10),
                   ("e_lfanew",     LONG)]

class e32_exe(ctypes.Structure):
    """
    A structure representing a e32_exe entry.
    """
    _fields_    = [("e32_magic",        ctypes.c_ubyte * 4),
                   ("e32_cpu",          ctypes.c_ushort),
                   ("e32_objcnt",       ctypes.c_ushort),
                   ("e32_timestamp",    ctypes.c_ulong),
                   ("e32_symtaboff",    ctypes.c_ulong),
                   ("e32_symcount",     ctypes.c_ulong),
                   ("e32_opthdrsize",   ctypes.c_ushort),
                   ("e32_imageflags",   ctypes.c_ushort),
                   ("e32_coffmagic",    ctypes.c_ushort),
                   ("e32_linkmajor",    ctypes.c_ubyte),
                   ("e32_linkminor",    ctypes.c_ubyte),
                   ("e32_codesize",     ctypes.c_ulong),
                   ("e32_initdsize",    ctypes.c_ulong),
                   ("e32_uninitdsize",  ctypes.c_ulong),
                   ("e32_entryrva",     ctypes.c_ulong),
                   ("e32_codebase",     ctypes.c_ulong),
                   ("e32_database",     ctypes.c_ulong),
                   ("e32_vbase",        ctypes.c_ulong),
                   ("e32_objalign",     ctypes.c_ulong),
                   ("e32_filealign",    ctypes.c_ulong),
                   ("e32_osmajor",      ctypes.c_ushort),
                   ("e32_osminor",      ctypes.c_ushort),
                   ("e32_usermajor",    ctypes.c_ushort),
                   ("e32_userminor",    ctypes.c_ushort),
                   ("e32_subsysmajor",  ctypes.c_ushort),
                   ("e32_subsysminor",  ctypes.c_ushort),
                   ("e32_res1",         ctypes.c_ulong),
                   ("e32_vsize",        ctypes.c_ulong),
                   ("e32_hdrsize",      ctypes.c_ulong),
                   ("e32_filechksum",   ctypes.c_ulong),
                   ("e32_subsys",       ctypes.c_ushort),
                   ("e32_dllflags",     ctypes.c_ushort),
                   ("e32_stackmax",     ctypes.c_ulong),
                   ("e32_stackinit",    ctypes.c_ulong),
                   ("e32_heapmax",      ctypes.c_ulong),
                   ("e32_heapinit",     ctypes.c_ulong),
                   ("e32_res2",         ctypes.c_ulong),
                   ("e32_hdrextra",     ctypes.c_ulong),
                   ("e32_unit",         info * _STD_EXTRA)]

class o32_obj(ctypes.Structure):
    """
    A structure for representing an o32_obj entry.
    """
    _fields_    = [("o32_name",     ctypes.c_ubyte * _E32OBJNAMEBYTES),
                   ("o32_vsize",    ctypes.c_ulong),
                   ("o32_rva",      ctypes.c_ulong),
                   ("o32_psize",    ctypes.c_ulong),
                   ("o32_dataptr",  ctypes.c_ulong),
                   ("o32_realaddr", ctypes.c_ulong),
                   ("o32_access",   ctypes.c_ulong),
                   ("o32_temp3",    ctypes.c_ulong),
                   ("o32_flags",    ctypes.c_ulong)]

class file_entry(ctypes.Structure):
    """
    A structure representing a file entry.
    """
    _fields_    = [("dwFileAttributes", DWORD),
                   ("ftTime",           filetime),
                   ("nRealFileSize",    DWORD),
                   ("nCompFileSize",    DWORD),
                   ("lpszFileName",     DWORD),
                   ("ulLoadOffset",     ULONG)]

def read_dword(data, offset):
    """
    Reads a dword size of bytes from the data buffer starting
    at the given offset.

    Parameters:
    data (bytes): A continous sequence of bytes
    offset (int): An offset to start

    Returns:
    int: A dword size of bytes interpreted as a number
    """
    return int.from_bytes(data[offset:offset + ctypes.sizeof(DWORD)], sys.byteorder)

def load_from_offset(data, offset, structure):
    """
    Loads information from the given sequence of bytes and offset into a specified
    structure type.

    Parameters:
    data (bytes): A continous sequence of bytes
    offset (int): The offset into the data
    structure (type): A type of structure to create and fill

    Returns:
    ctypes.Structure: A structure that is to be filled from the bytes at the given offset
    """
    return structure.from_buffer_copy(data[offset:offset + ctypes.sizeof(structure)])

def read_null_terminated_string(data, offset, encoding='ascii'):
    """
    Returns a null terminated string starting from the given offset
    into the given data.

    Parameters:
    data (bytes): A continous sequence of bytes
    offset (int): Offset to start looking
    encoding (string): An encoding to interpret the string

    Returns:
    string: The found string
    """
    start   = offset
    current = offset
    while data[current] != 0:
        current += 1

    return data[start:current].decode(encoding)

def write_dummy_mz_header(f):
    """
    Writes a image DOS header to the given file.

    Parameters:
    f (file): File to write to

    Returns:
    None
    """
    dos = image_dos_header()

    dos.e_magic     = _IMAGE_DOS_SIGNATURE
    dos.e_cblp      = 0x90
    dos.e_cp        = 3
    dos.e_cparhdr   = 0x4
    dos.e_maxalloc  = 0xffff
    dos.e_sp        = 0xb8
    dos.e_lfarlc    = 0x40
    dos.e_lfanew    = 0xc0

    doscode = bytes([0x0e, 0x1f, 0xba, 0x0e, 0x00, 0xb4, 0x09, 0xcd, 0x21, 0xb8, 0x01, 0x4c, 0xcd, 0x21, 0x54, 0x68,
            0x69, 0x73, 0x20, 0x70, 0x72, 0x6f, 0x67, 0x72, 0x61, 0x6d, 0x20, 0x63, 0x61, 0x6e, 0x6e, 0x6f,
            0x74, 0x20, 0x62, 0x65, 0x20, 0x72, 0x75, 0x6e, 0x20, 0x69, 0x6e, 0x20, 0x44, 0x4f, 0x53, 0x20,
            0x6d, 0x6f, 0x64, 0x65, 0x2e, 0x0d, 0x0d, 0x0a, 0x24, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

    f.write(dos)
    f.write(doscode)
    write_blanks(f, 0x40)

def filetime_to_time_t(pft):
    """
    Converts filetime structure to time_t value.

    Parameters:
    pft (filetime): filetime structure
    
    Returns:
    int: time_t value
    """
    t = pft.dwHighDateTime
    t <<= 32
    t |= pft.dwLowDateTime
    t //= 10000000
    t -= 11644473600

    return t

def write_alignment(f, page_size):
    """
    Writes blanks to the given file to fill the current page size gap.

    Parameters:
    f (file): File to write to
    page_size (int): A page size

    Returns:
    None
    """
    cur_ofs = f.tell()
    if cur_ofs % page_size != 0:
        write_blanks(f, page_size - (cur_ofs % page_size))

def write_blanks(f, n_blanks):
    """
    Extends the current file by n_blanks amount of bytes from the current position.

    Parameters:
    f (file): File to extend
    n_blanks (int): Number of bytes to extend by

    Returns:
    None
    """
    f.seek(n_blanks, io.SEEK_CUR)

class WinceExtract(binwalk.core.plugin.Plugin):

    MODULES = ['Signature']

    ROM_SIGNATURE       = 0x43454345
    ROM_DESCRIPTION_RE  = re.compile(r"^windows ce memory segment header, toc address: 0x([0-9a-fA-F]+)$", re.IGNORECASE)
    SEGMENT_NAMES       = [".text", ".data", ".pdata", ".rsrc", ".other"]

    def init(self):
        """
        Initializes this plugin for binwalk. Adds an extractor rule for a
        Windows CE ROM file. If running 32-bit Python, it will load
        dlls required to decompress Windows CE ROM files.

        Parameters:
        None

        Returns:
        None
        """
        if self.module.extractor.enabled:
            self.module.extractor.add_rule(txtrule=None,
                                           regex=WinceExtract.ROM_DESCRIPTION_RE.pattern,
                                           extension="bin",
                                           recurse=False,
                                           cmd=self.extractor)

        self.image_start    = None
        self.cedecompress   = None 
        """ Current dependency on CECompress.dll requires an x86 Windows system. """
        if (binwalk.core.common.MSWindows() == True and platform.architecture()[0] == "32bit"): 
            try:
                self.CECOMPRESS     = cdll.LoadLibrary("CECompress.dll")
                self.cedecompress   = self.CECOMPRESS.CEDecompressROM          
            except Exception:
                print("No DLL")
                pass
            

    def scan(self, result):
        """
        Called everytime binwalk finds a signature in a file. If the signature
        is a Windows CE ROM header, the offset will be saved.

        Parameters:
        result (binwalk.core.magic.SignatureResult): A signature result from a file

        Returns:
        None
        """
        if self.image_start is None:
            match = WinceExtract.ROM_DESCRIPTION_RE.match(result.description)
            if match is not None:
                self.image_start = result.offset

    def extractor(self, fname):
        """
        Called when a file matches the extraction criteria set by the init method.
        This should be called after the scan has been called for a Windows CE ROM header.
        
        Reads and extracts files from a Windows CE ROM file.

        Parameters:
        fname (string): The filename of Windows CE ROM file

        Returns:
        None
        """
        infile      = os.path.abspath(fname)
        indir       = os.path.dirname(infile)
        size        = os.path.getsize(infile)
        self.data   = bytearray(size - self.image_start)

        with open(infile, 'rb') as f:
            f.readinto(self.data)

        self.load_offset    = read_dword(self.data, _SIGNATURE_OFFSET + 4) - read_dword(self.data, _SIGNATURE_OFFSET + 8)
        self.romhdr_offset  = self.minus_load_offset(read_dword(self.data, _SIGNATURE_OFFSET + 4))
        romhdr_s            = load_from_offset(self.data, self.romhdr_offset, romhdr)

        for i in range(romhdr_s.nummods):
            # Offset romhdr[1] + toc_entry[i]
            toc_s       = load_from_offset(self.data, self.romhdr_offset + ctypes.sizeof(romhdr) + (ctypes.sizeof(toc_entry)*i), toc_entry)
            filename    = read_null_terminated_string(self.data, self.minus_load_offset(toc_s.lpszFileName))
            
            e32_s           = load_from_offset(self.data, self.minus_load_offset(toc_s.ulE32Offset), e32_rom)
            self.o32_offset = self.minus_load_offset(toc_s.ulO32Offset)
            o32_s           = load_from_offset(self.data, self.o32_offset, o32_rom)
            
            if self.cedecompress is not None:
                self.extract_file(romhdr_s, toc_s, os.path.join(indir, filename), e32_s, o32_s)

        # Offset romhdr[1] + toc_entry[romhdr_s.nummods]
        toc_f_offset = self.romhdr_offset + ctypes.sizeof(romhdr) + (ctypes.sizeof(toc_entry) * romhdr_s.nummods)

        for i in range(romhdr_s.numfiles):
            toc_f_s     = load_from_offset(self.data, toc_f_offset + (ctypes.sizeof(file_entry) * i), file_entry)
            filename    = read_null_terminated_string(self.data, self.minus_load_offset(toc_f_s.lpszFileName))

            if self.cedecompress is not None:
                with open(os.path.join(indir, filename), 'w+b') as f:
                    self.write_uncompressed_data(f, self.minus_load_offset(toc_f_s.ulLoadOffset), toc_f_s.nCompFileSize,
                        toc_f_s.nCompFileSize != toc_f_s.nRealFileSize, toc_f_s.nRealFileSize)

        del self.data

    def minus_load_offset(self, offset):
        """
        Gives back an offset that was subtracted by the currently
        known loading offset.

        Parameters:
        offset (int): A given offset

        Returns:
        int: The given offset subtracted by a known load offset
        """
        return offset - self.load_offset

    def extract_file(self, rom, toc, name, e32, o32):
        """
        Extracts certain files from a Windows CE ROM file. It seems that
        this is only used when extracting modules.

        Parameters:
        rom (romhdr): A romhdr structure
        toc (toc_entry): A toc_entry structure
        name (string): An absolute file path
        e32 (e32_rom): An e32_rom structure
        o32 (o32_rom): AN o32_rom structure

        Returns:
        None
        """
        with open(name, 'w+b') as f:
            write_dummy_mz_header(f)
            dw_e32_ofs = f.tell()
            self.write_e32_header(f, rom, e32, toc, o32)

            o32_ofs_list    = []
            data_ofs_list   = []
            data_len_list   = []

            self.segment_name_usage = [0, 0, 0, 0, 0]
            for i in range(e32.e32_objcnt):
                o32_ofs_list.append(f.tell())
                o32_s   = load_from_offset(self.data, self.o32_offset + (ctypes.sizeof(o32_rom) * i), o32_rom)
                rva     = self.write_o32_header(f, e32, o32_s)

            write_alignment(f, 0x200)

            dw_header_size = f.tell()

            for i in range(e32.e32_objcnt):
                o32_s = load_from_offset(self.data, self.o32_offset + (ctypes.sizeof(o32_rom) * i), o32_rom)
                data_ofs_list.append(f.tell())

                data_len = self.write_uncompressed_data(f, self.minus_load_offset(o32_s.o32_dataptr), min(o32_s.o32_vsize, o32_s.o32_psize), 
                    (o32_s.o32_flags & _IMAGE_SCN_COMPRESSED) != 0, o32_s.o32_vsize)
            
                data_len_list.append(data_len)
                write_alignment(f, 0x200)

            dw_total_file_size = f.tell()

            for i in range(e32.e32_objcnt):
                f.seek(o32_ofs_list[i] + 16, io.SEEK_SET)
                f.write(data_len_list[i].to_bytes(ctypes.sizeof(DWORD), sys.byteorder))
                f.write(data_ofs_list[i].to_bytes(ctypes.sizeof(DWORD), sys.byteorder))

                f.seek(dw_e32_ofs + 0x54, io.SEEK_SET) # ofs to e32_hdrsize
                f.write(dw_header_size.to_bytes(ctypes.sizeof(DWORD), sys.byteorder))
                f.seek(dw_total_file_size, io.SEEK_SET)

    def write_e32_header(self, f, rom, e32, t, o32):
        """
        Writes an e32 object to the file.

        Parameters:
        f (file): File to write to
        rom (romhdr): A romhdr structure
        e32 (e32_rom): A e32_rom structure
        t (toc_entry): A toc_entry structure
        o32 (o32_rom): A o32_rom structure

        Returns:
        None
        """
        pe32 = e32_exe()

        pe32.e32_magic[0]       = ord('P')
        pe32.e32_magic[1]       = ord('E')
        pe32.e32_cpu            = rom.usCPUType
        pe32.e32_objcnt         = e32.e32_objcnt
        pe32.e32_timestamp      = filetime_to_time_t(t.ftTime)
        pe32.e32_symtaboff      = 0
        pe32.e32_symcount       = 0
        pe32.e32_opthdrsize     = 0xe0
        pe32.e32_imageflags     = e32.e32_imageflags | _IMAGE_FILE_RELOCS_STRIPPED
        pe32.e32_coffmagic      = 0x10b
        pe32.e32_linkmajor      = 6
        pe32.e32_linkminor      = 1
        pe32.e32_codesize       = self.calc_segment_size_sum(e32.e32_objcnt, _IMAGE_SCN_CNT_CODE)
        pe32.e32_initdsize      = self.calc_segment_size_sum(e32.e32_objcnt, _IMAGE_SCN_CNT_INITIALIZED_DATA)
        pe32.e32_uninitdsize    = self.calc_segment_size_sum(e32.e32_objcnt, _IMAGE_SCN_CNT_UNINITIALIZED_DATA)
        pe32.e32_entryrva       = e32.e32_entryrva
        pe32.e32_codebase       = self.find_first_segment(e32.e32_objcnt, _IMAGE_SCN_CNT_CODE)
        pe32.e32_database       = self.find_first_segment(e32.e32_objcnt, _IMAGE_SCN_CNT_INITIALIZED_DATA)
        pe32.e32_vbase          = e32.e32_vbase
        pe32.e32_objalign       = 0x1000
        pe32.e32_filealign      = 0x200
        pe32.e32_osmajor        = 4
        pe32.e32_osminor        = 0
        pe32.e32_subsysmajor    = e32.e32_subsysmajor
        pe32.e32_subsysminor    = e32.e32_subsysminor
        pe32.e32_vsize          = e32.e32_vsize
        pe32.e32_filechksum     = 0
        pe32.e32_subsys         = e32.e32_subsys
        pe32.e32_stackmax       = e32.e32_stackmax
        pe32.e32_stackinit      = 0x1000
        pe32.e32_heapmax        = 0x100000
        pe32.e32_heapinit       = 0x1000
        pe32.e32_hdrextra       = _STD_EXTRA

        pe32.e32_unit[_EXP]         = e32.e32_unit[_EXP]
        pe32.e32_unit[_IMP]         = e32.e32_unit[_IMP]
        pe32.e32_unit[_RES]         = e32.e32_unit[_RES]
        pe32.e32_unit[_EXC]         = e32.e32_unit[_EXC]
        pe32.e32_unit[_SEC]         = e32.e32_unit[_SEC]
        pe32.e32_unit[_IMD]         = e32.e32_unit[_IMD]
        pe32.e32_unit[_MSP]         = e32.e32_unit[_MSP]
        pe32.e32_unit[_RS4].rva     = e32.e32_sect14rva
        pe32.e32_unit[_RS4].size    = e32.e32_sect14size

        f.write(pe32)

    def write_o32_header(self, f, e32, o32):
        """
        Writes an o32 object to the file.

        Parameters:
        f (file): File to write to
        e32 (e32_rom): A e32_rom structure
        o32 (o32_rom): A o32_rom structure

        Returns:
        int: An o32_obj rva
        """
        po32 = o32_obj()

        if e32.e32_unit[_RES].rva == o32.o32_rva and e32.e32_units[_RES].size == o32.o32_vsize:
            seg_type = _ST_RSRC
        elif e32.e32_unit[_EXC].rva == o32.o32_rva and e32.e32_unit[_EXC].size == o32.o32_vsize:
            seg_type = _ST_PDATA
        elif (o32.o32_flags & _IMAGE_SCN_CNT_CODE) != 0:
            seg_type = _ST_TEXT
        elif (o32.o32_flags & _IMAGE_SCN_CNT_INITIALIZED_DATA) != 0:
            seg_type = _ST_DATA
        elif (o32.o32_flags & _IMAGE_SCN_CNT_UNINITIALIZED_DATA) != 0:
            seg_type = _ST_PDATA
        else:
            seg_type = _ST_OTHER

        segment_name = WinceExtract.SEGMENT_NAMES[seg_type]
        if self.segment_name_usage[seg_type] != 0:
            segment_name += '{}'.format(self.segment_name_usage[seg_type])

        po32.o32_name[:] = segment_name.encode('ascii')[:_E32OBJNAMEBYTES].ljust(_E32OBJNAMEBYTES, '\0'.encode('ascii'))

        self.segment_name_usage[seg_type] += 1

        po32.o32_vsize      = o32.o32_vsize
        po32.o32_rva        = o32.o32_realaddr - e32.e32_vbase
        po32.o32_psize      = 0
        po32.o32_dataptr    = 0
        po32.o32_realaddr   = 0
        po32.o32_access     = 0
        po32.o32_temp3      = 0
        po32.o32_flags      = o32.o32_flags & (~_IMAGE_SCN_COMPRESSED)

        f.write(po32)

        return po32.o32_rva

    def calc_segment_size_sum(self, objcnt, segtypeflag):
        """
        Sums up all the o32 objects' vsize that match the segment type flags.

        Parameters:
        objcnt (int): The amount of o32 objects
        segtypeflag (int): A flag of some sort

        Returns:
        int: Sum of vsizes
        """
        size = 0
        for i in range(objcnt):
            o32_s = load_from_offset(self.data, self.o32_offset + (ctypes.sizeof(o32_rom) * i), o32_rom)
            if (o32_s.o32_flags & segtypeflag) != 0:
                size += o32_s.o32_vsize

        return size

    def find_first_segment(self, objcnt, segtypeflag):
        """
        Finds the first o32 that matches the given segment type flags.

        Parameters:
        objcnt (int): The amount of o32 objects
        segtypeflag (int): The current flags to check

        Returns:
        int: The o32 rva of the o32 object that matches the given flag,
            otherwise 0
        """
        for i in range(objcnt):
            o32_s = load_from_offset(self.data, self.o32_offset + (ctypes.sizeof(o32_rom) * i), o32_rom)
            if (o32_s.o32_flags & segtypeflag) != 0:
                return o32_s.o32_rva
        
        return 0

    def write_uncompressed_data(self, f, offset, datasize, bCompressed, maxUncompressedSize):
        """
        Uses the CEDecompress Windows library function to decompress the ROM data and write
        out its files.

        Parameters:
        f (file): File to write to
        offset (int): The beginning of the o32_rom object
        datasize (int): Size of the o32_rom object
        bCompressed (bool): Whether the contents are compressed and need to be decompressed first
        maxUncompressedSize (int): The amount of data to uncompress

        Returns:
        int: How many bytes were written
        """
        buf = bytes(self.data[offset:offset + datasize])

        buflen = datasize
        if datasize != maxUncompressedSize and bCompressed:
            dcbuf   = bytes(maxUncompressedSize + 4096)
            buflen  = self.cedecompress(buf, datasize, dcbuf, maxUncompressedSize, 0, 1, 4096) # CALL TO EXTERNAL LIBRARY

            if buflen != _CEDECOMPRESS_FAILED:
                buf = dcbuf
            else:
                print("error decompressing {:08x}L{:08x}", dataptr, datasize)
                buflen = datasize

        nWritten = f.write(buf[:buflen])
        if nWritten != buflen:
            print("error writing uncompressed data")

        return nWritten

