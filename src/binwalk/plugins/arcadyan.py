import os
import binwalk.core.common
import binwalk.core.plugin


class ArcadyanDeobfuscator(binwalk.core.plugin.Plugin):

    '''
    Deobfuscator for known Arcadyan firmware obfuscation(s).
    '''
    MODULES = ['Signature']

    OBFUSCATION_MAGIC_SIZE = 4
    MAX_IMAGE_SIZE = 0x1B0000
    BLOCK_SIZE = 32
    BLOCK1_OFFSET = 4
    BLOCK2_OFFSET = 0x68
    MIN_FILE_SIZE = (OBFUSCATION_MAGIC_SIZE + BLOCK2_OFFSET + BLOCK_SIZE)

    BLOCK1_START = BLOCK1_OFFSET
    BLOCK1_END = BLOCK1_START + BLOCK_SIZE

    BLOCK2_START = BLOCK2_OFFSET
    BLOCK2_END = BLOCK2_OFFSET + BLOCK_SIZE

    P1_START = 0
    P1_END = BLOCK1_OFFSET

    P2_START = BLOCK1_END
    P2_END = BLOCK2_START

    P3_START = BLOCK2_END

    def init(self):
        if self.module.extractor.enabled:
            self.module.extractor.add_rule(regex="^obfuscated arcadyan firmware",
                extension="obfuscated",
                cmd=self.extractor)

    def extractor(self, fname):
        deobfuscated = None
        fname = os.path.abspath(fname)

        infile = binwalk.core.common.BlockFile(fname, "rb")
        obfuscated = infile.read(self.MIN_FILE_SIZE)
        infile.close()

        if os.path.getsize(fname) > self.MAX_IMAGE_SIZE:
            raise Exception("Input file too large for Arcadyan obfuscated firmware")

        if len(obfuscated) >= self.MIN_FILE_SIZE:
            # Swap blocks 1 and 2
            p1 = obfuscated[self.P1_START:self.P1_END]
            b1 = obfuscated[self.BLOCK1_START:self.BLOCK1_END]
            p2 = obfuscated[self.P2_START:self.P2_END]
            b2 = obfuscated[self.BLOCK2_START:self.BLOCK2_END]
            p3 = obfuscated[self.P3_START:]
            deobfuscated = p1 + b2 + p2 + b1 + p3

            # Nibble-swap each byte in block 1
            nswap = ''
            for i in range(self.BLOCK1_START, self.BLOCK1_END):
                nswap += chr(((ord(deobfuscated[i]) & 0x0F) << 4) + ((ord(deobfuscated[i]) & 0xF0) >> 4))
            deobfuscated = deobfuscated[
                self.P1_START:self.P1_END] + nswap + deobfuscated[self.BLOCK1_END:]

            # Byte-swap each byte pair in block 1
            bswap = ''
            i = self.BLOCK1_START
            while i < self.BLOCK1_END:
                bswap += deobfuscated[i + 1] + deobfuscated[i]
                i += 2
            deobfuscated = deobfuscated[
                self.P1_START:self.P1_END] + bswap + deobfuscated[self.BLOCK1_END:]

        if deobfuscated:
            out = binwalk.core.common.BlockFile((os.path.splitext(fname)[0] + '.deobfuscated'), "wb")
            out.write(deobfuscated)
            out.close()
            return True
        else:
            return False
