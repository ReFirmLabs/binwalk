import capstone
import binwalk.core.common
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
                   long='disasm',
                   kwargs={'enabled' : True},
                   description='Identify executable code using the capstone disassembler'),
            Option(short='T',
                   long='minsn',
                   type=int,
                   kwargs={'min_insn_count' : 0},
                   description='Minimum number of instructions to be considered valid'),
          ]

    KWARGS = [
                Kwarg(name='enabled', default=False),
                Kwarg(name='min_insn_count', default=0),
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
        if not self.min_insn_count:
            self.min_insn_count = self.DEFAULT_MIN_INSN_COUNT

    def scan_file(self, fp):
        total_read = 0

        while True:
            (data, dlen) = fp.read_block()
            if not data:
                break

            offset = 0
            while offset < dlen:
                for arch in self.ARCHITECTURES:
                    md = capstone.Cs(arch.type, (arch.mode + arch.endianess))
                    ninsn = len([insn for insn in md.disasm_lite(data[offset:offset+(self.min_insn_count*10)], 0)])
                    binwalk.core.common.debug("0x%.8X   %s, at least %d valid instructions" % ((total_read+offset), arch.description, ninsn))

                    if ninsn >= self.min_insn_count:
                        description = arch.description + ", at least %d valid instructions" % ninsn
                        r = self.result(offset=total_read+offset, file=fp, description=description)
                        if r.valid and r.display and not self.config.verbose:
                            return

                offset += 1

            total_read += dlen

    def run(self):
        for fp in iter(self.next_file, None):
            self.header()
            self.scan_file(fp)
            self.footer()

