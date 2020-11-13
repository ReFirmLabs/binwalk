import capstone
import binwalk.core.common
import binwalk.core.compat
from binwalk.core.module import Module, Option, Kwarg


class ArchResult(object):

    def __init__(self, **kwargs):
        for (k, v) in binwalk.core.compat.iterator(kwargs):
            setattr(self, k, v)


class Architecture(object):

    def __init__(self, **kwargs):
        for (k, v) in binwalk.core.compat.iterator(kwargs):
            setattr(self, k, v)


class Disasm(Module):

    THRESHOLD = 10
    DEFAULT_MIN_INSN_COUNT = 500

    TITLE = "Disassembly Scan"
    ORDER = 10

    CLI = [
        Option(short='Y',
               long='disasm',
               kwargs={'enabled': True},
               description='Identify the CPU architecture of a file using the capstone disassembler'),
        Option(short='T',
               long='minsn',
               type=int,
               kwargs={'min_insn_count': 0},
               description='Minimum number of consecutive instructions to be considered valid (default: %d)' % DEFAULT_MIN_INSN_COUNT),
        Option(long='continue',
               short='k',
               kwargs={'keep_going': True},
               description="Don't stop at the first match"),
    ]

    KWARGS = [
        Kwarg(name='enabled', default=False),
        Kwarg(name='keep_going', default=False),
        Kwarg(name='min_insn_count', default=DEFAULT_MIN_INSN_COUNT),
    ]

    ARCHITECTURES = [
        Architecture(type=capstone.CS_ARCH_ARM,
                     mode=capstone.CS_MODE_ARM,
                     endianness=capstone.CS_MODE_BIG_ENDIAN,
                     description="ARM executable code, 32-bit, big endian"),
        Architecture(type=capstone.CS_ARCH_ARM,
                     mode=capstone.CS_MODE_ARM,
                     endianness=capstone.CS_MODE_LITTLE_ENDIAN,
                     description="ARM executable code, 32-bit, little endian"),
        Architecture(type=capstone.CS_ARCH_ARM64,
                     mode=capstone.CS_MODE_ARM,
                     endianness=capstone.CS_MODE_BIG_ENDIAN,
                     description="ARM executable code, 64-bit, big endian"),
        Architecture(type=capstone.CS_ARCH_ARM64,
                     mode=capstone.CS_MODE_ARM,
                     endianness=capstone.CS_MODE_LITTLE_ENDIAN,
                     description="ARM executable code, 64-bit, little endian"),

        Architecture(type=capstone.CS_ARCH_PPC,
                     mode=capstone.CS_MODE_BIG_ENDIAN,
                     endianness=capstone.CS_MODE_BIG_ENDIAN,
                     description="PPC executable code, 32/64-bit, big endian"),

        Architecture(type=capstone.CS_ARCH_MIPS,
                     mode=capstone.CS_MODE_64,
                     endianness=capstone.CS_MODE_BIG_ENDIAN,
                     description="MIPS executable code, 32/64-bit, big endian"),
        Architecture(type=capstone.CS_ARCH_MIPS,
                     mode=capstone.CS_MODE_64,
                     endianness=capstone.CS_MODE_LITTLE_ENDIAN,
                     description="MIPS executable code, 32/64-bit, little endian"),

        Architecture(type=capstone.CS_ARCH_ARM,
                     mode=capstone.CS_MODE_THUMB,
                     endianness=capstone.CS_MODE_LITTLE_ENDIAN,
                     description="ARM executable code, 16-bit (Thumb), little endian"),
        Architecture(type=capstone.CS_ARCH_ARM,
                     mode=capstone.CS_MODE_THUMB,
                     endianness=capstone.CS_MODE_BIG_ENDIAN,
                     description="ARM executable code, 16-bit (Thumb), big endian"),
    ]

    def init(self):
        self.disassemblers = []

        if not self.min_insn_count:
            self.min_insn_count = self.DEFAULT_MIN_INSN_COUNT

        self.disasm_data_size = self.min_insn_count * 10

        for arch in self.ARCHITECTURES:
            self.disassemblers.append((capstone.Cs(arch.type, (arch.mode + arch.endianness)), arch.description))

    def scan_file(self, fp):
        total_read = 0

        while True:
            result = None

            (data, dlen) = fp.read_block()
            if dlen < 1:
                break

            # If this data block doesn't contain at least two different bytes, skip it
            # to prevent false positives (e.g., "\x00\x00\x00\x00" is a nop in
            # MIPS).
            if len(set(data)) >= 2:
                block_offset = 0

                # Loop through the entire block, or until we're pretty sure
                # we've found some valid code in this block
                while (block_offset < dlen) and (result is None or result.count < self.THRESHOLD):
                    # Don't pass the entire data block into disasm_lite, it's horribly inefficient
                    # to pass large strings around in Python. Break it up into
                    # smaller code blocks instead.
                    code_block = binwalk.core.compat.str2bytes(data[block_offset:block_offset + self.disasm_data_size])

                    # If this code block doesn't contain at least two different bytes, skip it
                    # to prevent false positives (e.g., "\x00\x00\x00\x00" is a
                    # nop in MIPS).
                    if len(set(code_block)) >= 2:
                        for (md, description) in self.disassemblers:
                            insns = [insn for insn in md.disasm_lite(code_block, (total_read + block_offset))]
                            binwalk.core.common.debug("0x%.8X   %s, at least %d valid instructions" % ((total_read + block_offset),
                                                                                 description,
                                                                                 len(insns)))

                            # Did we disassemble at least self.min_insn_count
                            # instructions?
                            if len(insns) >= self.min_insn_count:
                                # If we've already found the same type of code
                                # in this block, simply update the result
                                # counter
                                if result and result.description == description:
                                    result.count += 1
                                    if result.count >= self.THRESHOLD:
                                        break
                                else:
                                    result = ArchResult(offset=total_read +
                                        block_offset + fp.offset,
                                        description=description,
                                        insns=insns,
                                        count=1)

                    block_offset += 1
                    self.status.completed += 1

                if result is not None:
                    r = self.result(offset=result.offset,
                                    file=fp,
                                    description=(result.description + ", at least %d valid instructions" % len(result.insns)))

                    if r.valid and r.display:
                        if self.config.verbose:
                            for (position, size, mnem, opnds) in result.insns:
                                self.result(offset=position, file=fp, description="%s %s" % (mnem, opnds))
                        if not self.keep_going:
                            return

            total_read += dlen
            self.status.completed = total_read

    def run(self):
        for fp in iter(self.next_file, None):
            self.header()
            self.scan_file(fp)
            self.footer()
