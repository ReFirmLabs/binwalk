import capstone
import binwalk.core.common
import binwalk.core.compat
from binwalk.core.module import Module, Option, Kwarg

class Architecture(object):
    def __init__(self, **kwargs):
        for (k, v) in kwargs.iteritems():
            setattr(self, k, v)

class CodeID(Module):

    DEFAULT_MIN_INSN_COUNT = 500

    TITLE = "Disassembly Scan"
    ORDER = 10

    CLI = [
            Option(short='Y',
                   long='code',
                   kwargs={'enabled' : True},
                   description='Attempts to identify the CPU architecture of a file using the capstone disassembler'),
            Option(short='T',
                   long='minsn',
                   type=int,
                   kwargs={'min_insn_count' : 0},
                   description='Minimum number of consecutive instructions to be considered valid (default: %d)' % DEFAULT_MIN_INSN_COUNT),
            Option(short='V',
                   long='disasm',
                   kwargs={'show_disasm' : True},
                   description='Display the disassembled instructions'),
          ]

    KWARGS = [
                Kwarg(name='enabled', default=False),
                Kwarg(name='show_disasm', default=False),
                Kwarg(name='min_insn_count', default=DEFAULT_MIN_INSN_COUNT),
             ]

    ARCHITECTURES = [
                    Architecture(type=capstone.CS_ARCH_MIPS,
                                 mode=capstone.CS_MODE_32,
                                 endianess=capstone.CS_MODE_BIG_ENDIAN,
                                 description="MIPS executable code, 32-bit, big endian"),
                    Architecture(type=capstone.CS_ARCH_MIPS,
                                 mode=capstone.CS_MODE_32,
                                 endianess=capstone.CS_MODE_LITTLE_ENDIAN,
                                 description="MIPS executable code, 32-bit, little endian"),
                    Architecture(type=capstone.CS_ARCH_ARM,
                                 mode=capstone.CS_MODE_ARM,
                                 endianess=capstone.CS_MODE_BIG_ENDIAN,
                                 description="ARM executable code, 32-bit, big endian"),
                    Architecture(type=capstone.CS_ARCH_ARM,
                                 mode=capstone.CS_MODE_ARM,
                                 endianess=capstone.CS_MODE_LITTLE_ENDIAN,
                                 description="ARM executable code, 32-bit, little endian"),
                    Architecture(type=capstone.CS_ARCH_PPC,
                                 mode=capstone.CS_MODE_BIG_ENDIAN,
                                 endianess=capstone.CS_MODE_BIG_ENDIAN,
                                 description="PPC executable code, 32/64-bit, big endian"),

                    #Architecture(type=capstone.CS_ARCH_MIPS,
                    #             mode=capstone.CS_MODE_16,
                    #             endianess=capstone.CS_MODE_BIG_ENDIAN,
                    #             description="MIPS executable code, 16-bit, big endian"),
                    #Architecture(type=capstone.CS_ARCH_MIPS,
                    #             mode=capstone.CS_MODE_16,
                    #             endianess=capstone.CS_MODE_LITTLE_ENDIAN,
                    #             description="MIPSEL executable code, 16-bit, little endian"),
                    Architecture(type=capstone.CS_ARCH_ARM,
                                 mode=capstone.CS_MODE_THUMB,
                                 endianess=capstone.CS_MODE_LITTLE_ENDIAN,
                                 description="ARM executable code, 16-bit (Thumb), little endian"),
                    Architecture(type=capstone.CS_ARCH_ARM,
                                 mode=capstone.CS_MODE_THUMB,
                                 endianess=capstone.CS_MODE_BIG_ENDIAN,
                                 description="ARM executable code, 16-bit (Thumb), big endian"),

                    Architecture(type=capstone.CS_ARCH_MIPS,
                                 mode=capstone.CS_MODE_64,
                                 endianess=capstone.CS_MODE_BIG_ENDIAN,
                                 description="MIPS executable code, 64-bit, big endian"),
                    Architecture(type=capstone.CS_ARCH_MIPS,
                                 mode=capstone.CS_MODE_64,
                                 endianess=capstone.CS_MODE_LITTLE_ENDIAN,
                                 description="MIPS executable code, 64-bit, little endian"),
                    Architecture(type=capstone.CS_ARCH_ARM64,
                                 mode=capstone.CS_MODE_ARM,
                                 endianess=capstone.CS_MODE_BIG_ENDIAN,
                                 description="ARM executable code, 64-bit, big endian"),
                    Architecture(type=capstone.CS_ARCH_ARM64,
                                 mode=capstone.CS_MODE_ARM,
                                 endianess=capstone.CS_MODE_LITTLE_ENDIAN,
                                 description="ARM executable code, 64-bit, little endian"),
                    ]

    def init(self):
        self.disassemblers = []

        if not self.min_insn_count:
            self.min_insn_count = self.DEFAULT_MIN_INSN_COUNT

        self.disasm_data_size = self.min_insn_count * 10

        for arch in self.ARCHITECTURES:
            self.disassemblers.append((capstone.Cs(arch.type, (arch.mode + arch.endianess)), arch.description))

    def scan_file(self, fp):
        total_read = 0

        while True:
            (data, dlen) = fp.read_block()
            if not data:
                break

            # If this data block doesn't contain at least two different bytes, skip it
            # to prevent false positives (e.g., "\x00\x00\x00x\00" is a nop in MIPS).
            if len(set(data)) >= 2:
                block_offset = 0
                while block_offset < dlen:
                    # Don't pass the entire data block into disasm_lite, it's horribly inefficient
                    # to pass large strings around in Python. Break it up into smaller code blocks instead.
                    code_block = binwalk.core.compat.str2bytes(data[block_offset:block_offset+self.disasm_data_size])

                    # If this code block doesn't contain at least two different bytes, skip it
                    # to prevent false positives (e.g., "\x00\x00\x00x\00" is a nop in MIPS).
                    if len(set(code_block)) >= 2:
                        for (md, description) in self.disassemblers:
                            insns = [insn for insn in md.disasm_lite(code_block, (total_read+block_offset))]
                            binwalk.core.common.debug("0x%.8X   %s, at least %d valid instructions" % ((total_read+block_offset), description, len(insns)))

                            if len(insns) >= self.min_insn_count:
                                r = self.result(offset=total_read+block_offset, file=fp, description=(description + ", at least %d valid instructions" % len(insns)))
                                if r.valid and r.display:
                                    if self.show_disasm:
                                        for (position, size, mnem, opnds) in insns:
                                            self.result(offset=position, file=fp, description="\t%s %s" % (mnem, opnds))
                                    if not self.config.verbose:
                                        return


                    block_offset += 1

            total_read += dlen

    def run(self):
        for fp in iter(self.next_file, None):
            self.header()
            self.scan_file(fp)
            self.footer()

