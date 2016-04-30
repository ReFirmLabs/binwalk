import os
import subprocess
import binwalk.core.plugin

class CPIOPlugin(binwalk.core.plugin.Plugin):
    '''
    Ensures that ASCII CPIO archive entries only get extracted once.
    Also provides an internal CPIO extraction wrapper around the Unix
    cpio utility since no output directory can be provided to it directly.
    '''
    CPIO_OUT_DIR = "cpio-root"

    MODULES = ['Signature']

    def init(self):
        self.consecutive_hits = 0

        if self.module.extractor.enabled:
            self.module.extractor.add_rule(regex="^ascii cpio archive",
                                           extension="cpio",
                                           cmd=self.extractor,
                                           recurse=False)       # Most CPIO archives are file systems, so don't recurse into the extracted contents

    def extractor(self, fname):
        result = None
        fname = os.path.abspath(fname)
        out_dir = os.path.join(os.path.dirname(fname), self.CPIO_OUT_DIR)

        try:
            fpin = open(fname, "rb")
            fperr = open(os.devnull, "rb")
            os.mkdir(out_dir)
        except OSError:
            return

        try:
            curdir = os.getcwd()
            os.chdir(out_dir)
        except OSError:
            return

        try:
            result = subprocess.call(['cpio', '-d', '-i', '--no-absolute-filenames'],
                                     stdin=fpin,
                                     stderr=fperr,
                                     stdout=fperr)
        except OSError:
            result = -1

        os.chdir(curdir)
        fpin.close()
        fperr.close()

        if result in [0, 2]:
            return True
        else:
            return False

    def pre_scan(self):
        # Be sure to re-set this at the beginning of every scan
        self.found_archive = False
        self.found_archive_in_file = None

    def scan(self, result):
        if result.valid:
            # ASCII CPIO archives consist of multiple entries, ending with an entry named 'TRAILER!!!'.
            # Displaying each entry is useful, as it shows what files are contained in the archive,
            # but we only want to extract the archive when the first entry is found.
            if result.description.startswith('ASCII cpio archive'):
                self.consecutive_hits += 1

                if not self.found_archive or self.found_archive_in_file != result.file.name:
                    # This is the first entry. Set found_archive and allow the scan to continue normally.
                    self.found_archive_in_file = result.file.name
                    self.found_archive = True
                    result.extract = True
                elif 'TRAILER!!!' in result.description:
                    # This is the last entry, un-set found_archive.
                    self.found_archive = False
                    result.extract = False
                    self.consecutive_hits = 0
                else:
                    # The first entry has already been found and this is not the last entry, or the last entry
                    # has not yet been found. Don't extract.
                    result.extract = False
            elif self.consecutive_hits < 4:
                # If this was a valid non-CPIO archive result, reset these values; else, a previous
                # false positive CPIO result could leave these set, causing a subsequent valid CPIO
                # result to not be extracted.
                self.found_archive = False
                self.found_archive_in_file = None
                self.consecutive_hits = 0
            elif self.consecutive_hits >= 4:
                # Ignore other stuff until the end of CPIO is found
                # TODO: It would be better to jump to the end of this CPIO entry rather than make this assumption...
                result.valid = False
