import struct

import binwalk.core.plugin

class MWOS9_68000Validate(binwalk.core.plugin.Plugin):
    # This module does a header parity check to verify it is a OS-9 module
    parity = 0

    def _header_parity(self, string):
        parity = 0
        shorts = struct.unpack('>'+'H'*24, string)
        for short in shorts:
            parity ^= short
        return ~parity
    def scan(self, result):
        if result.description.lower().startswith('microware os-9/68000 module'):
            fd = self.module.config.open_file(result.file.path, offset=result.offset)
            words = binwalk.core.compat.str2bytes(fd.read(48))
            fd.close()

            if self._header_parity(words) & 0xFFFF != 0:
                result.valid = False
