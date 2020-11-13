#!/usr/bin/env python

import struct
import string
import binwalk.core.plugin
import binwalk.core.compat
import binwalk.core.common
try:
    # Requires the pycrypto library
    from Crypto.Cipher import DES
except ImportError as e:
    DES = None


class HilinkDecryptor(binwalk.core.plugin.Plugin):

    '''
    Plugin to decrypt, validate, and extract Hilink encrypted firmware.
    '''
    MODULES = ["Signature"]

    DES_KEY = "H@L9K*(3"
    SIGNATURE_DESCRIPTION = "Encrypted Hilink uImage firmware".lower()

    def init(self):
        if DES is None:
            self.enabled = False
        else:
            self.enabled = True

        if self.enabled is True and self.module.extractor.enabled is True:
            # Add an extraction rule for encrypted Hilink firmware signature
            # results
            self.module.extractor.add_rule(regex="^%s" % self.SIGNATURE_DESCRIPTION,
                extension="enc",
                cmd=self._decrypt_and_extract)

    def _decrypt_and_extract(self, fname):
        '''
        This does the extraction (e.g., it decrypts the image and writes it to a new file on disk).
        '''
        with open(fname, "r") as fp_in:
            encrypted_data = fp_in.read()

            decrypted_data = self._hilink_decrypt(encrypted_data)

            with open(binwalk.core.common.unique_file_name(fname[:-4], "dec"), "w") as fp_out:
                fp_out.write(decrypted_data)

    def _hilink_decrypt(self, encrypted_firmware):
        '''
        This does the actual decryption.
        '''
        cipher = DES.new(self.DES_KEY, DES.MODE_ECB)

        p1 = encrypted_firmware[0:3]
        p2 = encrypted_firmware[3:]
        p2 += b"\x00" * (8 - (len(p2) % 8))

        d1 = p1 + cipher.decrypt(p2)
        d1 += b"\x00" * (8 - (len(d1) % 8))

        return cipher.decrypt(d1)

    def scan(self, result):
        '''
        Validate signature results.
        '''
        if self.enabled is True:
            if result.valid is True:
                if result.description.lower().startswith(self.SIGNATURE_DESCRIPTION) is True:
                    # Read in the first 64 bytes of the suspected encrypted
                    # uImage header
                    fd = self.module.config.open_file(result.file.path, offset=result.offset)
                    encrypted_header_data = binwalk.core.compat.str2bytes(fd.read(64))
                    fd.close()

                    # Decrypt the header
                    decrypted_header_data = self._hilink_decrypt(encrypted_header_data)

                    # Pull out the image size and image name fields from the decrypted uImage header
                    # and add them to the printed description.
                    result.size = struct.unpack(b">L", decrypted_header_data[12:16])[0]
                    result.description += ", size: %d" % (result.size)
                    # NOTE: The description field should be 32 bytes? Hilink seems to use only 24 bytes for this field,
                    #       even though the header size is still 64 bytes?
                    result.description += ', image name: "%s"' % binwalk.core.compat.bytes2str(decrypted_header_data[32:56]).strip("\x00")

                    # Do some basic validation on the decrypted size and image
                    # name fields
                    if result.size > (result.file.size - result.offset):
                        result.valid = False
                    if not all(c in string.printable for c in result.description):
                        result.valid = False
