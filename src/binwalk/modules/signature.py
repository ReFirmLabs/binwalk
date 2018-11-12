# Basic signature scan module. This is the default (and primary) feature
# of binwalk.
import binwalk.core.magic
from binwalk.core.module import Module, Option, Kwarg


class Signature(Module):

    TITLE = "Signature Scan"
    ORDER = 10

    CLI = [
        Option(short='B',
               long='signature',
               kwargs={'enabled': True, 'explicit_signature_scan': True},
               description='Scan target file(s) for common file signatures'),
        Option(short='R',
               long='raw',
               kwargs={'enabled': True, 'raw_bytes': []},
               type=list,
               dtype=str.__name__,
               description='Scan target file(s) for the specified sequence of bytes'),
        Option(short='A',
               long='opcodes',
               kwargs={'enabled': True, 'search_for_opcodes': True},
               description='Scan target file(s) for common executable opcode signatures'),
        Option(short='m',
               long='magic',
               kwargs={'enabled': True, 'magic_files': []},
               type=list,
               dtype='file',
               description='Specify a custom magic file to use'),
        Option(short='b',
               long='dumb',
               kwargs={'dumb_scan': True},
               description='Disable smart signature keywords'),
        Option(short='I',
               long='invalid',
               kwargs={'show_invalid': True},
               description='Show results marked as invalid'),
        Option(short='x',
               long='exclude',
               kwargs={'exclude_filters': []},
               type=list,
               dtype=str.__name__,
               description='Exclude results that match <str>'),
        Option(short='y',
               long='include',
               kwargs={'include_filters': []},
               type=list,
               dtype=str.__name__,
               description='Only show results that match <str>'),
    ]

    KWARGS = [
        Kwarg(name='enabled', default=False),
        Kwarg(name='show_invalid', default=False),
        Kwarg(name='include_filters', default=[]),
        Kwarg(name='exclude_filters', default=[]),
        Kwarg(name='raw_bytes', default=[]),
        Kwarg(name='search_for_opcodes', default=False),
        Kwarg(name='explicit_signature_scan', default=False),
        Kwarg(name='dumb_scan', default=False),
        Kwarg(name='magic_files', default=[]),
    ]

    VERBOSE_FORMAT = "%s    %d"

    def init(self):
        self.one_of_many = None

        # Append the user's magic file first so that those signatures take
        # precedence
        if self.search_for_opcodes:
            self.magic_files = [
                self.config.settings.user.binarch,
                self.config.settings.system.binarch,
            ]

        # Use the system default magic file if no other was specified, or if -B
        # was explicitly specified
        if (not self.magic_files and not self.raw_bytes) or self.explicit_signature_scan:
            self.magic_files += self.config.settings.user.magic + \
                self.config.settings.system.magic

        # Initialize libmagic
        self.magic = binwalk.core.magic.Magic(include=self.include_filters,
                                              exclude=self.exclude_filters,
                                              invalid=self.show_invalid)

        # Create a signature from the raw bytes, if any
        if self.raw_bytes:
            raw_signatures = []
            for raw_bytes in self.raw_bytes:
                raw_signatures.append("0    string    %s    Raw signature (%s)" % (raw_bytes, raw_bytes))
            binwalk.core.common.debug("Parsing raw signatures: %s" % str(raw_signatures))
            self.magic.parse(raw_signatures)

        # Parse the magic file(s)
        if self.magic_files:
            binwalk.core.common.debug("Loading magic files: %s" % str(self.magic_files))
            for f in self.magic_files:
                self.magic.load(f)

        self.VERBOSE = ["Signatures:", len(self.magic.signatures)]

    def validate(self, r):
        '''
        Called automatically by self.result.
        '''
        if self.show_invalid:
            r.valid = True
        elif r.valid:
            if not r.description:
                r.valid = False

            if r.size and (r.size + r.offset) > r.file.size:
                r.valid = False

            if r.jump and (r.jump + r.offset) > r.file.size:
                r.valid = False

            if hasattr(r, "location") and (r.location != r.offset):
                r.valid = False

        if r.valid:
            # Don't keep displaying signatures that repeat a bunch of times
            # (e.g., JFFS2 nodes)
            if r.id == self.one_of_many:
                r.display = False
            elif r.many:
                self.one_of_many = r.id
            else:
                self.one_of_many = None

    def scan_file(self, fp):
        self.one_of_many = None
        self.magic.reset()

        while True:
            (data, dlen) = fp.read_block()
            if dlen < 1:
                break

            current_block_offset = 0
            block_start = fp.tell() - dlen
            self.status.completed = block_start - fp.offset

            # Scan this data block for magic signatures
            for r in self.magic.scan(data, dlen):
                # current_block_offset is set when a jump-to-offset keyword is encountered while
                # processing signatures. This points to an offset inside the current data block
                # that scanning should jump to, so ignore any subsequent candidate signatures that
                # occur before this offset inside the current data block.
                if r.offset < current_block_offset:
                    continue

                # Keep a record of the relative offset of this signature inside the current data block
                # (used later for setting current_block_offset).
                relative_offset = r.offset + r.adjust

                # Set the absolute offset inside the target file
                r.offset = block_start + relative_offset

                # Provide an instance of the current file object
                r.file = fp

                # Register the result for futher processing/display
                # self.result automatically calls self.validate for result
                # validation
                self.result(r=r)

                # If a sigure specified the end tag, jump to the end of the file
                if r.end == True:
                    r.jump = fp.size

                # Is this a valid result and did it specify a jump-to-offset
                # keyword, and are we doing a "smart" scan?
                if r.valid and r.jump > 0 and not self.dumb_scan:
                    absolute_jump_offset = r.offset + r.jump
                    current_block_offset = relative_offset + r.jump

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
