#! /usr/bin/env python3

"""

WinCE Decompressor: Decompress compressed files from Windows CE ROMs.

"""

import csv
import ctypes
import io
import os
import argparse

class UnsupportedWindowSizeRange(Exception):
    """
    Exception to deal with window sizes out of range.
    """
    def __init__(self):
        super().__init__()


class LZXConstants(object):
    """
    A class to hold constants relating to LZX compression/decompression.
    """
    PRETREE_NUM_ELEMENTS = 20
    SECONDARY_NUM_ELEMENTS = 249
    ALIGNED_NUM_ELEMENTS = 8
    NUM_PRIMARY_LENGTHS = 7

    NUM_CHARS = 256

    MIN_MATCH = 2
    MAX_MATCH = 257

    NUM_REPEATED_OFFSETS = 3
    MAX_GROWTH = 6144

    E8_DISABLE_THRESHOLD = 32768

    class BlockTypeEnum(object):
        """
        An enum type for the different types of blocks in LZX.
        """
        def __init__(self, value):
            self.value = value

        def __eq__(self, other):
            if not isinstance(other, LZXConstants.BlockTypeEnum):
                return False
            return self.value == other.value

        def __ne__(self, other):
            return not self.__eq__(other)

        def __hash__(self):
            return hash(self.value)

    BLOCKTYPE_INVALID = BlockTypeEnum(0)
    BLOCKTYPE_VERBATIM = BlockTypeEnum(1)
    BLOCKTYPE_ALIGNED = BlockTypeEnum(2)
    BLOCKTYPE_UNCOMPRESSED = BlockTypeEnum(3)

    PRETREE_MAXSYMBOLS = PRETREE_NUM_ELEMENTS
    PRETREE_TABLEBITS = 6
    PRETREE_MAX_CODEWORD = 16
    MAINTREE_MAXSYMBOLS = NUM_CHARS + (51 << 3)
    MAINTREE_TABLEBITS = 11
    MAINTREE_MAX_CODEWORD = 16
    LENTREE_MAXSYMBOLS = SECONDARY_NUM_ELEMENTS
    LENTREE_TABLEBITS = 10
    LENTREE_MAX_CODEWORD = 16
    ALIGNTREE_MAXSYMBOLS = ALIGNED_NUM_ELEMENTS
    ALIGNTREE_TABLEBITS = 7
    ALIGNTREE_MAX_CODEWORD = 8

    LENTABLE_SAFETY = 64
    position_slots = [30, 32, 34, 36, 38, 42, 50, 66, 98, 162, 290]
    extra_bits = \
        [
            0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8,
            9, 9, 10, 10, 11, 11, 12, 12, 13, 13, 14, 14, 15, 15, 16, 16,
            17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17
        ]
    position_base = \
        [
            0, 1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512,
            768, 1024, 1536, 2048, 3072, 4096, 6144, 8192, 12288, 16384, 24576, 32768,
            49152, 65536, 98304, 131072, 196608, 262144, 393216, 524288, 655360,
            786432, 917504, 1048576, 1179648, 1310720, 1441792, 1572864, 1703936,
            1835008, 1966080, 2097152
        ]


class LZXState(object):
    """
    Holds the current state of LZX decompression.
    """
    def __init__(self, window):
        if window < 15 or window > 21:
            raise UnsupportedWindowSizeRange()

        self.R0 = 1
        self.R1 = 1
        self.R2 = 1
        self.main_elements = LZXConstants.NUM_CHARS + (LZXConstants.position_slots[window - 15] << 3)
        self.header_read = False
        self.block_type = LZXConstants.BLOCKTYPE_INVALID
        self.block_length = 0
        self.block_remaining = 0
        self.frames_read = 0
        self.intel_filesize = 0
        self.intel_curpos = 0
        self.intel_started = False

        self.pretree_table = [0] * ((1 << LZXConstants.PRETREE_TABLEBITS) + (LZXConstants.PRETREE_MAXSYMBOLS << 1))
        self.pretree_len = [0] * (LZXConstants.PRETREE_MAXSYMBOLS + LZXConstants.LENTABLE_SAFETY)
        self.maintree_table = [0] * ((1 << LZXConstants.MAINTREE_TABLEBITS) + (LZXConstants.MAINTREE_MAXSYMBOLS << 1))
        self.maintree_len = [0] * (LZXConstants.MAINTREE_MAXSYMBOLS + LZXConstants.LENTABLE_SAFETY)
        self.lentree_table = [0] * ((1 << LZXConstants.LENTREE_TABLEBITS) + (LZXConstants.LENTREE_MAXSYMBOLS << 1))
        self.lentree_len = [0] * (LZXConstants.LENTREE_MAXSYMBOLS + LZXConstants.LENTABLE_SAFETY)
        self.aligntree_table = [0] * (
                (1 << LZXConstants.ALIGNTREE_TABLEBITS) + (LZXConstants.ALIGNTREE_MAXSYMBOLS << 1))
        self.aligntree_len = [0] * (LZXConstants.ALIGNTREE_MAXSYMBOLS + LZXConstants.LENTABLE_SAFETY)

        self.window_size = 1 << (window & 0x1f)
        self.actual_size = self.window_size
        self.window = bytearray(b'\xDC') * self.window_size
        self.window_posn = 0


class LZXDecoder(object):
    def __init__(self, window):
        self.state = LZXState(window)

    def decompress(self, in_f, in_len, out_f, out_len):
        """
        Decompresses an input file.

        :param in_f: Compressed input file
        :param in_len: Length of compressed input file
        :param out_f: Decompressed output file
        :param out_len: Length of decompressed output file

        :return: Status of function
        """
        bit_buf = LZXDecoder.BitBuffer(in_f)
        start_pos = in_f.tell()
        end_pos = start_pos + in_len

        togo = out_len

        '''
        The header consists of either a zero bit indicating no encoder preprocessing, or a one bit followed by a 
        file translation size, a value which is used in encoder preprocessing.
        '''
        if not self.state.header_read:
            intel = bit_buf.read_bits(1)
            if intel == 1:
                i = bit_buf.read_bits(16)
                j = bit_buf.read_bits(16)
                self.state.intel_filesize = (i << 16) | j
            self.state.header_read = True

        while togo > 0:
            if self.state.block_remaining == 0:
                if self.state.block_type == LZXConstants.BLOCKTYPE_UNCOMPRESSED:
                    if (self.state.block_length & 1) == 1:
                        in_f.seek(1, os.SEEK_CUR)
                    self.state.block_type = LZXConstants.BLOCKTYPE_INVALID
                    bit_buf.reset()

                self.state.block_type = LZXConstants.BlockTypeEnum(bit_buf.read_bits(3))
                self.state.block_length = bit_buf.read_bits(24)
                self.state.block_remaining = self.state.block_length

                if self.state.block_type == LZXConstants.BLOCKTYPE_ALIGNED:
                    for i in range(0, 8):
                        self.state.aligntree_len[i] = bit_buf.read_bits(3)

                    self.__make_decode_table(LZXConstants.ALIGNTREE_MAXSYMBOLS, LZXConstants.ALIGNTREE_TABLEBITS,
                                             self.state.aligntree_len, self.state.aligntree_table)

                if self.state.block_type == LZXConstants.BLOCKTYPE_VERBATIM or \
                        self.state.block_type == LZXConstants.BLOCKTYPE_ALIGNED:
                    self.__read_lengths(self.state.maintree_len, 0, 256, bit_buf)
                    self.__read_lengths(self.state.maintree_len, 256, self.state.main_elements, bit_buf)
                    LZXDecoder.__make_decode_table(LZXConstants.MAINTREE_MAXSYMBOLS, LZXConstants.MAINTREE_TABLEBITS,
                                                   self.state.maintree_len, self.state.maintree_table)
                    if self.state.maintree_len[0xE8] != 0:
                        self.state.intel_started = True

                    self.__read_lengths(self.state.lentree_len, 0, LZXConstants.SECONDARY_NUM_ELEMENTS, bit_buf)
                    LZXDecoder.__make_decode_table(LZXConstants.LENTREE_MAXSYMBOLS, LZXConstants.LENTREE_TABLEBITS,
                                                   self.state.lentree_len, self.state.lentree_table)
                elif self.state.block_type == LZXConstants.BLOCKTYPE_UNCOMPRESSED:
                    if end_pos <= in_f.tell() + 4:
                        return -1

                    self.state.intel_started = True
                    bit_buf.ensure_bits(16)
                    if bit_buf.bits_left > 16:
                        in_f.seek(-2, os.SEEK_CUR)

                    self.state.R0 = int.from_bytes(in_f.read(4), byteorder='little')
                    self.state.R1 = int.from_bytes(in_f.read(4), byteorder='little')
                    self.state.R2 = int.from_bytes(in_f.read(4), byteorder='little')
                else:
                    return -1

            if in_f.tell() > start_pos + in_len:
                if in_f.tell() > start_pos + in_len + 2 or bit_buf.bits_left < 16:
                    return -1

            togo -= self.state.block_remaining if self.state.block_remaining > togo else togo

            self.state.window_posn &= self.state.window_size - 1
            if self.state.window_posn + self.state.block_remaining > self.state.window_size:
                return -1

            if self.state.block_type == LZXConstants.BLOCKTYPE_VERBATIM or \
                    self.state.block_type == LZXConstants.BLOCKTYPE_ALIGNED:
                # Block Type: Verbatim or Aligned
                self.__decompress_block(bit_buf)
            elif self.state.block_type == LZXConstants.BLOCKTYPE_UNCOMPRESSED:
                # Block Type: Uncompressed
                if in_f.tell() >= end_pos:
                    return -1
                self.__decompress_uncompress(in_f)
            else:
                return -1

        if togo != 0:
            return -1

        start_window_pos = self.state.window_size if self.state.window_posn == 0 else self.state.window_posn
        start_window_pos -= out_len
        out_f.write(memoryview(self.state.window)[start_window_pos:start_window_pos + out_len])

        '''
        The encoder may optionally perform a preprocessing stage on all input blocks which improves compression on 
        Intel x86 code. The preprocessing translates x86 CALL instructions to use absolute offsets instead of 
        relative offsets. Therefore must be translated back to relative offsets after decompression.
        '''
        self.undo_e8_preprocessing(out_len, out_f)

        return 0

    def undo_e8_preprocessing(self, out_len, out_f):
        """
        Translates x86 CALL instruction offsets from absolute to relative.

        :param out_len: Output file length
        :param out_f: Output file

        :return: None
        """
        if out_len >= 10 and self.state.intel_started:
            out_f.seek(0)
            i = 0
            '''
            E8 preprocessing does not appear to be disabled after the 32768th chunk of a XIP compressed file, 
            which is another difference from the LZX compression used in cabinet files.
            '''
            while i < out_len - 10:
                byte = int.from_bytes(out_f.read(1), byteorder='little')
                if byte == 0xE8:
                    absolute_offset = int.from_bytes(out_f.read(4), byteorder='little', signed=True)
                    '''Values in the range of -2^31 to i and intel_filesize to +2^31 are left unchanged.'''
                    if -i <= absolute_offset < self.state.intel_filesize:
                        absolute_offset += -i if absolute_offset >= 0 else self.state.intel_filesize
                        out_f.seek(-4, os.SEEK_CUR)
                        out_f.write(absolute_offset.to_bytes(4, byteorder='little', signed=True))
                    i += 4
                i += 1

    def __read_lengths(self, lens, first, last, bit_buf):
        """
        Reads the pretree from the input, then uses the pretree to decode lens length values from the input.

        :param lens: Decode table length
        :param first: first index of the given length table
        :param last: last index of the given length table
        :param bit_buf: Input bitstream

        :return: None
        """
        for x in range(0, 20):
            self.state.pretree_len[x] = bit_buf.read_bits(4)

        LZXDecoder.__make_decode_table(LZXConstants.PRETREE_MAXSYMBOLS, LZXConstants.PRETREE_TABLEBITS,
                                       self.state.pretree_len, self.state.pretree_table)

        x = first

        while x < last:
            z = self.__read_huff_sym_pretree(bit_buf)
            if z == 17:
                y = bit_buf.read_bits(4) + 4
                for _ in range(y):
                    lens[x] = 0
                    x += 1
            elif z == 18:
                y = bit_buf.read_bits(5) + 20
                for _ in range(y):
                    lens[x] = 0
                    x += 1
            elif z == 19:
                y = bit_buf.read_bits(1) + 4
                z = self.__read_huff_sym_pretree(bit_buf)
                z = (lens[x] + 17 - z) % 17
                for _ in range(y):
                    lens[x] = z
                    x += 1
            else:
                z = (lens[x] + 17 - z) % 17
                lens[x] = z
                x += 1

    @staticmethod
    def __read_huff_sym(table, lengths, nsyms, nbits, bit_buf, codeword):
        """
        Reads and returns the next Huffman-encoded symbol from a bitstream.

        :param table: Decode table
        :param lengths: Decode table length
        :param nsyms: Decode table's max symbols
        :param nbits: Decode table bit length
        :param bit_buf: Input bitstream
        :param codeword: Codeword length

        :return: Huffman-encoded symbol
        """
        bit_buf.ensure_bits(codeword)
        i = table[bit_buf.peek_bits(nbits)]
        if i >= nsyms:
            j = 1 << (LZXDecoder.BitBuffer.buffer_num_bits - nbits)
            while True:
                j >>= 1
                i <<= 1
                i |= 1 if (bit_buf.buffer.value & j) != 0 else 0
                if j == 0:
                    return 0
                i = table[i]
                if i < nsyms:
                    break

        j = lengths[i]
        bit_buf.remove_bits(j)
        return i

    def __read_huff_sym_pretree(self, bit_buf):
        """
        Reads and returns the next Huffman-encoded symbol from a bitstream using the PreTree.

        :param bit_buf: Input bitstream
        :return: Huffman-encoded symbol
        """
        return self.__read_huff_sym(self.state.pretree_table, self.state.pretree_len,
                                    LZXConstants.PRETREE_MAXSYMBOLS, LZXConstants.PRETREE_TABLEBITS, bit_buf,
                                    LZXConstants.PRETREE_MAX_CODEWORD)

    def __read_huff_sym_maintree(self, bit_buf):
        """
        Reads and returns the next Huffman-encoded symbol from a bitstream using the MainTree.

        :param bit_buf: Input bitstream
        :return: Huffman-encoded symbol
        """
        return self.__read_huff_sym(self.state.maintree_table, self.state.maintree_len,
                                    LZXConstants.MAINTREE_MAXSYMBOLS, LZXConstants.MAINTREE_TABLEBITS, bit_buf,
                                    LZXConstants.MAINTREE_MAX_CODEWORD)

    def __read_huff_sym_lentree(self, bit_buf):
        """
        Reads and returns the next Huffman-encoded symbol from a bitstream using the LengthTree.

        :param bit_buf: Input bitstream
        :return: Huffman-encoded symbol
        """
        return self.__read_huff_sym(self.state.lentree_table, self.state.lentree_len,
                                    LZXConstants.LENTREE_MAXSYMBOLS, LZXConstants.LENTREE_TABLEBITS, bit_buf,
                                    LZXConstants.LENTREE_MAX_CODEWORD)

    def __read_huff_sym_aligntree(self, bit_buf):
        """
        Reads and returns the next Huffman-encoded symbol from a bitstream using the AlignedTree.

        :param bit_buf: Input bitstream
        :return: Huffman-encoded symbol
        """
        return self.__read_huff_sym(self.state.aligntree_table, self.state.aligntree_len,
                                    LZXConstants.ALIGNTREE_MAXSYMBOLS, LZXConstants.ALIGNTREE_TABLEBITS, bit_buf,
                                    LZXConstants.ALIGNTREE_MAX_CODEWORD)

    @staticmethod
    def __make_decode_table(nsyms, nbits, length, table):
        """
        Build a decoding table for a Huffman code.

        :param nsyms: Decode table's max symbols
        :param nbits: Decode table bit length
        :param length: Decode table length
        :param table: Decode table

        :return: Function status
        """
        bit_num = 1
        pos = 0
        table_mask = 1 << nbits
        bit_mask = table_mask >> 1
        next_symbol = bit_mask

        while bit_num <= nbits:
            for sym in range(nsyms):
                if length[sym] == bit_num:
                    leaf = pos
                    pos += bit_mask

                    if pos > table_mask:
                        return False

                    for _ in range(bit_mask):
                        table[leaf] = sym
                        leaf += 1

            bit_mask >>= 1
            bit_num += 1

        if pos != table_mask:
            for sym in range(pos, table_mask):
                table[sym] = 0

            pos <<= 16
            table_mask <<= 16
            bit_mask = 1 << 15

            while bit_num <= 16:
                for sym in range(nsyms):
                    if length[sym] == bit_num:
                        leaf = pos >> 16
                        for fill in range(bit_num - nbits):
                            if table[leaf] == 0:
                                table[next_symbol << 1] = 0
                                table[(next_symbol << 1) + 1] = 0
                                table[leaf] = next_symbol
                                next_symbol += 1
                            leaf = table[leaf] << 1
                            if ((pos >> (15 - fill)) & 1) == 1:
                                leaf += 1

                        table[leaf] = sym
                        pos += bit_mask
                        if pos > table_mask:
                            return False
                bit_mask >>= 1
                bit_num += 1

        if pos == table_mask:
            return True

        for sym in range(nsyms):
            if length[sym] != 0:
                return False

        return True

    def __decompress_block(self, bit_buf):
        """
        Decompresses an LZX-compressed block of data from which the header has already been read.

        :param bit_buf: Input bitstream

        :return: None
        """
        while self.state.block_remaining > 0:
            main_element = self.__read_huff_sym_maintree(bit_buf)
            if main_element < LZXConstants.NUM_CHARS:
                self.state.window[self.state.window_posn] = main_element
                self.state.window_posn += 1
                self.state.block_remaining -= 1
                continue

            main_element -= LZXConstants.NUM_CHARS

            match_length = main_element & LZXConstants.NUM_PRIMARY_LENGTHS
            if match_length == LZXConstants.NUM_PRIMARY_LENGTHS:
                length_footer = self.__read_huff_sym_lentree(bit_buf)
                match_length += length_footer

            match_length += LZXConstants.MIN_MATCH

            match_offset = main_element >> 3

            if match_offset > 2:
                extra = LZXConstants.extra_bits[match_offset]
                '''There is an error in the LZX "specification" at this
                point; it indicates that a Huffman symbol is to be 
                read only if num_extra_bits is greater than 3, but 
                actually it is if num_extra_bits is greater than or 
                equal to 3.'''
                if self.state.block_type == LZXConstants.BLOCKTYPE_ALIGNED and extra >= 3:
                    verbatim_bits = bit_buf.read_bits(extra - 3)
                    verbatim_bits <<= 3
                    aligned_bits = self.__read_huff_sym_aligntree(bit_buf)
                else:
                    '''For non-aligned blocks, or for aligned blocks with 
                    less than 3 extra bits, the extra bits are added 
                    directly to the match offset, and the correction for 
                    the alignment is taken to be 0.'''
                    verbatim_bits = bit_buf.read_bits(extra)
                    aligned_bits = 0

                '''Calculate the match offset'''
                match_offset = LZXConstants.position_base[match_offset] + verbatim_bits + aligned_bits - 2

                self.state.R2 = self.state.R1
                self.state.R1 = self.state.R0
                self.state.R0 = match_offset
            elif match_offset == 0:
                match_offset = self.state.R0
            elif match_offset == 1:
                match_offset = self.state.R1
                self.state.R1 = self.state.R0
                self.state.R0 = match_offset
            else:
                match_offset = self.state.R2
                self.state.R2 = self.state.R0
                self.state.R0 = match_offset

            rundest = self.state.window_posn
            self.state.block_remaining -= match_length

            if self.state.window_posn >= match_offset:
                runsrc = rundest - match_offset
            else:
                runsrc = rundest + (self.state.window_size - match_offset)
                copy_length = match_offset - self.state.window_posn
                if copy_length < match_length:
                    match_length -= copy_length
                    self.state.window_posn += copy_length
                    for _ in range(copy_length):
                        self.state.window[rundest] = self.state.window[runsrc]
                        rundest += 1
                        runsrc += 1
                    runsrc = 0

            self.state.window_posn += match_length

            for _ in range(match_length):
                self.state.window[rundest] = self.state.window[runsrc]
                rundest += 1
                runsrc += 1

    def __decompress_uncompress(self, in_f):
        """
        Processes an uncompressed block of data from which the header has already been read.

        :param in_f: Input file

        :return: None
        """
        in_f.readinto(
            memoryview(self.state.window)[self.state.window_posn:self.state.window_posn + self.state.block_remaining])
        self.state.window_posn += self.state.block_remaining

    class BitBuffer(object):
        buffer_type = ctypes.c_uint
        buffer_num_bits = ctypes.sizeof(buffer_type) * 8

        def __init__(self, f):
            # Need a fixed type integer for bit manipulation
            self.buffer = LZXDecoder.BitBuffer.buffer_type(0)
            self.bits_left = 0
            self.stream = f

        def reset(self):
            self.buffer.value = 0
            self.bits_left = 0

        def ensure_bits(self, bits):
            while self.bits_left < bits:
                lo = self.stream.read(1)
                hi = self.stream.read(1)

                lo = ord(lo) if len(lo) != 0 else 0
                hi = ord(hi) if len(hi) != 0 else 0

                self.buffer.value |= ((hi << 8) | lo) << (LZXDecoder.BitBuffer.buffer_num_bits - 16 - self.bits_left)
                self.bits_left += 16

        def peek_bits(self, bits):
            return self.buffer.value >> (LZXDecoder.BitBuffer.buffer_num_bits - (bits & 0x1f))

        def remove_bits(self, bits):
            self.buffer.value <<= bits
            self.bits_left -= bits

        def read_bits(self, bits):
            ret = 0

            if bits > 0:
                self.ensure_bits(bits)
                ret = self.peek_bits(bits)
                self.remove_bits(bits)

            return ret


def bin_decompress_rom(read_buffer, amount, decompressed_buffer):
    """
    Decompresses the given data using LZX and places it into the decompressed buffer.

    :param read_buffer: Compressed data buffer
    :param amount: Amount of bytes to decompress
    :param decompressed_buffer: Decompressed data buffer

    :return: The status of the function and the amount of bytes decompressed as a tuple
    """
    in_binary_memory_file = io.BytesIO(read_buffer)
    out_binary_memory_file = io.BytesIO()
    window_size = int.from_bytes(in_binary_memory_file.read(4), byteorder='little')
    decompressed_size = int.from_bytes(in_binary_memory_file.read(4), byteorder='little')

    int.from_bytes(in_binary_memory_file.read(8), byteorder='little')  # We do not need these 8 bytes of information, so we can move past it.

    decoder = LZXDecoder(window_size)
    status = decoder.decompress(in_binary_memory_file, amount, out_binary_memory_file, decompressed_size)
    out_binary_memory_file.seek(0)
    decompressed_buffer[:decompressed_size] = out_binary_memory_file.read(decompressed_size)
    return status, decompressed_size


# noinspection PyPep8Naming
def CEDecompressROM(read_buffer, compressed_size, decompressed_buffer, uncompressed_size, skip, step, blocksize):
    """
    Decompresses a section of a file extracted from a Windows CE ROM file.

    :param read_buffer: Input data buffer
    :param compressed_size: Overall size of the compressed data
    :param decompressed_buffer: Output data buffer
    :param uncompressed_size: Overall size of the decompressed data
    :param skip: How many initial blocks to skip
    :param step: How many bytes to step by
    :param blocksize: Maximum size of a block expected

    :return: The overall size of the decompressed data
    """
    output_position = 0
    block_bits = int(blocksize == 4096) * 2 + 10

    if step != 1 and step != 2:
        return -1

    if ((skip & ((1 << block_bits) - 1)) == 0) and compressed_size > 2:
        num_blocks = int.from_bytes(read_buffer[0:3], byteorder='little')
        if num_blocks == 0:
            num_blocks = 2
        else:
            num_blocks = (num_blocks - 1 >> (block_bits & 0x1f)) + 2

        current_position = num_blocks * 3
        next_position = skip >> (block_bits & 0x1f)
        if not (current_position <= compressed_size and next_position < num_blocks):
            return -1

        if next_position != 0:
            current_position = int.from_bytes(read_buffer[next_position * 3:next_position * 3 + 3], byteorder='little')

        blocksize = 0
        compressed_size = current_position
        input_position = (next_position + 1) * 3
        for current_block in range(next_position + 1, num_blocks):
            if uncompressed_size == 0:
                break

            current_position = int.from_bytes(read_buffer[input_position:input_position + 3], byteorder='little')
            input_position += 3
            (status, bytes_processed) = bin_decompress_rom(memoryview(read_buffer)[compressed_size:],
                                                           current_position - compressed_size,
                                                           memoryview(decompressed_buffer)[output_position:])
            if status != 0:
                return -1

            blocksize += bytes_processed
            output_position += bytes_processed * step
            uncompressed_size -= bytes_processed
            compressed_size = current_position
    else:
        return -1

    return blocksize


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', metavar='file_name', help='input file name')
    parser.add_argument('-o', metavar='uncompressed_dir', help='output uncompressed directory')
    parser.add_argument('-cs', metavar='compressed_file_size', type=int, help='compressed file size')
    parser.add_argument('-us', metavar='uncompressed_file_size', type=int, help='uncompressed file size')
    args = parser.parse_args()

    file_name = args.i
    uncompressed_dir = args.o
    compressed_file_size = args.cs
    uncompressed_file_size = args.us

    with open(file_name, 'r+b') as compressed_file:
        buf = compressed_file.read()
        dcbuf = bytearray(uncompressed_file_size + 4096)
        buflen = CEDecompressROM(buf, compressed_file_size, dcbuf, uncompressed_file_size, 0, 1, 4096)
        if buflen == -1:
            print(f'[ERROR] Failed to decompress: {file_name}')
            exit(1)
        else:
            base_name = os.path.basename(file_name)
            with open(os.path.join(uncompressed_dir, base_name),'w+b') as uncompressed_file:
                uncompressed_file.write(dcbuf[:buflen])