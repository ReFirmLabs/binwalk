# Basic signature scan module. This is the default (and primary) feature of binwalk.

import binwalk.core.magic
import binwalk.core.smart
import binwalk.core.parser
from binwalk.core.module import Module, Option, Kwarg

class Signature(Module):

    TITLE = "Signature Scan"
    ORDER = 10

    CLI = [
            Option(short='B',
                   long='signature',
                   kwargs={'enabled' : True, 'explicit_signature_scan' : True},
                   description='Scan target file(s) for common file signatures'),
            Option(short='R',
                   long='raw',
                   kwargs={'enabled' : True, 'raw_bytes' : ''},
                   type=str,
                   description='Scan target file(s) for the specified sequence of bytes'),
            Option(short='A',
                   long='opcodes',
                   kwargs={'enabled' : True, 'search_for_opcodes' : True},
                   description='Scan target file(s) for common executable opcode signatures'),
            Option(short='C',
                   long='cast',
                   kwargs={'enabled' : True, 'cast_data_types' : True},
                   description='Cast offsets as a given data type (use -y to specify the data type / endianness)'),
            Option(short='m',
                   long='magic',
                   kwargs={'enabled' : True, 'magic_files' : []},
                   type=list,
                   dtype='file',
                   description='Specify a custom magic file to use'),
            Option(short='b',
                   long='dumb',
                   kwargs={'dumb_scan' : True},
                   description='Disable smart signature keywords'),
    ]

    KWARGS = [
            Kwarg(name='enabled', default=False),
            Kwarg(name='raw_bytes', default=None),
            Kwarg(name='search_for_opcodes', default=False),
            Kwarg(name='explicit_signature_scan', default=False),
            Kwarg(name='cast_data_types', default=False),
            Kwarg(name='dumb_scan', default=False),
            Kwarg(name='magic_files', default=[]),
    ]

    VERBOSE_FORMAT = "%s    %d"

    def init(self):
        self.keep_going = self.config.keep_going

        # Create Signature and MagicParser class instances. These are mostly for internal use.
        self.smart = binwalk.core.smart.Signature(self.config.filter, ignore_smart_signatures=self.dumb_scan)
        self.parser = binwalk.core.parser.MagicParser(self.config.filter, self.smart)

        # If a raw byte sequence was specified, build a magic file from that instead of using the default magic files
        if self.raw_bytes is not None:
            self.magic_files = [self.parser.file_from_string(self.raw_bytes)]

        # Append the user's magic file first so that those signatures take precedence
        elif self.search_for_opcodes:
            self.magic_files = [
                    self.config.settings.user.binarch,
                    self.config.settings.system.binarch,
            ]

        elif self.cast_data_types:
            self.keep_going = True
            self.magic_files = [
                    self.config.settings.user.bincast,
                    self.config.settings.system.bincast,
            ]

        # Use the system default magic file if no other was specified, or if -B was explicitly specified
        if (not self.magic_files) or (self.explicit_signature_scan and not self.cast_data_types):
            self.magic_files.append(self.config.settings.user.binwalk)
            self.magic_files.append(self.config.settings.system.binwalk)

        # Parse the magic file(s) and initialize libmagic
        binwalk.core.common.debug("Loading magic files: %s" % str(self.magic_files))
        self.mfile = self.parser.parse(self.magic_files)
        self.magic = binwalk.core.magic.Magic(self.mfile, keep_going=self.keep_going)

        # Once the temporary magic files are loaded into libmagic, we don't need them anymore; delete the temp files
        if not binwalk.core.common.DEBUG:
            self.parser.rm_magic_files()

        self.VERBOSE = ["Signatures:", self.parser.signature_count]

    def validate(self, r):
        '''
        Called automatically by self.result.
        '''
        if not r.description:
            r.valid = False

        if r.size and (r.size + r.offset) > r.file.size:
            r.valid = False

        if r.jump and (r.jump + r.offset) > r.file.size:
            r.valid = False

        r.valid = self.config.filter.valid_result(r.description)

    def scan_file(self, fp):
        current_file_offset = 0

        while True:
            (data, dlen) = fp.read_block()
            if not data:
                break

            current_block_offset = 0
            block_start = fp.tell() - dlen
            self.status.completed = block_start - fp.offset

            for candidate_offset in self.parser.find_signature_candidates(data, dlen):

                # current_block_offset is set when a jump-to-offset keyword is encountered while
                # processing signatures. This points to an offset inside the current data block
                # that scanning should jump to, so ignore any subsequent candidate signatures that
                # occurr before this offset inside the current data block.
                if candidate_offset < current_block_offset:
                    continue

                # Pass the data to libmagic for parsing
                magic_result = self.magic.buffer(data[candidate_offset:candidate_offset+fp.block_peek_size])
                if not magic_result:
                    continue

                # The smart filter parser returns a binwalk.core.module.Result object
                r = self.smart.parse(magic_result)

                # Set the absolute offset inside the target file
                r.offset = block_start + candidate_offset + r.adjust

                # Provide an instance of the current file object
                r.file = fp

                # Register the result for futher processing/display
                # self.result automatically calls self.validate for result validation
                self.result(r=r)

                # Is this a valid result and did it specify a jump-to-offset keyword?
                if r.valid and r.jump > 0:
                    absolute_jump_offset = r.offset + r.jump
                    current_block_offset = candidate_offset + r.jump

                    # If the jump-to-offset is beyond the confines of the current block, seek the file to
                    # that offset and quit processing this block of data.
                    if absolute_jump_offset >= fp.tell():
                        fp.seek(r.offset + r.jump)
                        break

    def run(self):
        for fp in iter(self.next_file, None):
            self.header()
            self.scan_file(fp)
            self.footer()

        if hasattr(self, "magic") and self.magic:
            self.magic.close()

