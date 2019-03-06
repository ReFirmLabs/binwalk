import struct
import binascii
import binwalk.core.plugin
import binwalk.core.compat


class UBIValidPlugin(binwalk.core.plugin.Plugin):

    '''
    Helps validate UBI erase count signature results.

    Checks header CRC and calculates jump value
    '''
    MODULES = ['Signature']
    current_file = None
    last_ec_hdr_offset = None
    peb_size = None

    def _check_crc(self, ec_header):
        # Get the header's reported CRC value
        header_crc = struct.unpack(">I", ec_header[60:64])[0]

        # Calculate the actual CRC
        calculated_header_crc = ~binascii.crc32(ec_header[0:60]) & 0xffffffff

        # Make sure they match
        return header_crc == calculated_header_crc

    def _process_result(self, result):
        if self.current_file == result.file.path:
            result.display = False
        else:
            # Reset everything in case new file is encountered
            self.peb_size = None
            self.last_ec_hdr_offset = None
            self.peb_size = None

            # Display result and trigger extraction
            result.display = True

        self.current_file = result.file.path

        if not self.peb_size and self.last_ec_hdr_offset:
            # Calculate PEB size by subtracting last EC block offset
            self.peb_size = result.offset - self.last_ec_hdr_offset
        else:
            # First time plugin is called on file, save EC block offset
            self.last_ec_hdr_offset = result.offset

        if self.peb_size:
            # If PEB size has been determined jump PEB size
            result.jump = self.peb_size
        else:
            result.jump = 0

    def scan(self, result):
        if result.file and result.description.lower().startswith('ubi erase count header'):
            # Seek to and read the suspected UBI erase count header
            fd = self.module.config.open_file(result.file.path, offset=result.offset)

            ec_header = binwalk.core.compat.str2bytes(fd.read(1024))
            fd.close()

            result.valid = self._check_crc(ec_header[0:64])
            if result.valid:
                self._process_result(result)
