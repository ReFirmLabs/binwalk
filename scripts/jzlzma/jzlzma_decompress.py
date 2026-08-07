#!/usr/bin/env python3
"""Decompress Ingenic jzlzma (hardware LZ77 variant) files.

Detects and handles:
  - Raw jz_lzma_out.bin: [4B dict][4B uncomp_size][compressed stream]
  - mark_rootfs_lzma wrapper: [4B payload_size][4B magic 0x27051956][jz_lzma_out.bin]
  - Standard LZMA Alone streams (auto-detected by 0x5D prop byte)
"""
import struct, lzma, sys

kStartPosModelIndex, kEndPosModelIndex, kNumAlignBits = 4, 14, 4


def reverse_bits(n, bits):
    rev = 0
    for i in range(bits):
        rev <<= 1
        if n & (1 << i):
            rev |= 1
    return rev


def bit_stream(data):
    for byte in data:
        for bit in range(8):
            yield 1 if byte & (1 << bit) else 0


def read_num(stream, bits):
    num = 0
    for _ in range(bits):
        num = (num << 1) | next(stream)
    return num


def decode_length(stream):
    if next(stream) == 0:
        return read_num(stream, 3) + 2
    elif next(stream) == 0:
        return read_num(stream, 3) + 10
    else:
        return read_num(stream, 8) + 18


def decode_dist(stream):
    posSlot = read_num(stream, 6)
    if posSlot < kStartPosModelIndex:
        pos = posSlot
    else:
        numDirectBits = (posSlot >> 1) - 1
        pos = (2 | (posSlot & 1)) << numDirectBits
        if posSlot < kEndPosModelIndex:
            pos += reverse_bits(read_num(stream, numDirectBits), numDirectBits)
        else:
            pos += read_num(stream, numDirectBits - kNumAlignBits) << kNumAlignBits
            pos += reverse_bits(read_num(stream, kNumAlignBits), kNumAlignBits)
    return pos


def jzlzma_decompress(data):
    """Decompress jzlzma stream starting with compressed data (after header)."""
    stream = bit_stream(data)
    reps = [0, 0, 0, 0]
    decompressed = []
    try:
        while True:
            if next(stream) == 0:
                byte = read_num(stream, 8)
                decompressed.append(byte)
            else:
                size = 0
                if next(stream) == 0:
                    size = decode_length(stream)
                    reps.insert(0, decode_dist(stream))
                    reps.pop()
                elif next(stream) == 0:
                    if next(stream) == 0:
                        size = 1
                    else:
                        pass
                elif next(stream) == 0:
                    reps.insert(0, reps.pop(1))
                elif next(stream) == 0:
                    reps.insert(0, reps.pop(2))
                else:
                    reps.insert(0, reps.pop(3))

                if size == 0:
                    size = decode_length(stream)

                curLen = len(decompressed)
                start = curLen - reps[0] - 1
                while size > 0:
                    end = min(start + size, curLen)
                    decompressed.extend(decompressed[start:end])
                    size -= end - start
    except StopIteration:
        return bytes(decompressed)


def try_std_lzma(data):
    """Try standard LZMA Alone decompression."""
    try:
        decomp = lzma.LZMADecompressor(format=lzma.FORMAT_ALONE)
        return decomp.decompress(data)
    except Exception:
        return None


def detect_and_decompress(data):
    """Auto-detect format and decompress."""
    # Check for standard LZMA Alone header (starts with canonical prop byte 0x5D)
    if data[0] == 0x5D and len(data) > 13:
        result = try_std_lzma(data)
        if result is not None:
            return result, "standard LZMA"

    # Check for mark_rootfs_lzma wrapper: [4B size][4B magic 0x27051956]
    if len(data) > 8:
        magic_candidate = struct.unpack('<I', data[4:8])[0]
        if magic_candidate == 0x27051956:
            # Skip 8B wrapper + 4B dict + 4B uncomp_size to get compressed stream
            try:
                result = jzlzma_decompress(data[16:])
                if len(result) > 0:
                    return result, "jzlzma (wrapped)"
            except Exception:
                pass

    # Check for raw jzlzma (jz_lzma_out.bin): [4B dict][4B uncomp_size][stream]
    if len(data) > 8:
        dict_sz = struct.unpack('<I', data[:4])[0]
        if 0x1000 <= dict_sz <= 0x4000000:  # plausible dict size
            try:
                result = jzlzma_decompress(data[8:])
                if len(result) > 0:
                    return result, f"jzlzma (raw, dict=0x{dict_sz:x})"
            except Exception:
                pass

    # Try raw LZMA just in case
    result = try_std_lzma(data)
    if result is not None:
        return result, "standard LZMA"

    raise ValueError("Unknown compression format or corrupted data")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(f'Usage: {sys.argv[0]} in-file out-file [uncompressed-size]', file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1], 'rb') as f:
        data = f.read()

    result, method = detect_and_decompress(data)
    print(f"Decompressed using {method}: {len(result)} bytes -> {sys.argv[2]}", file=sys.stderr)
    with open(sys.argv[2], 'wb') as f:
        f.write(result)
