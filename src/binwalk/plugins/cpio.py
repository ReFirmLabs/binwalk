import os
import subprocess
import binwalk.core.common
import binwalk.core.plugin

class CPIOPlugin(binwalk.core.plugin.Plugin):

    '''
    Ensures that ASCII CPIO archive entries only get extracted once.
    Also provides an internal CPIO extraction wrapper around the Unix
    cpio utility since no output directory can be provided to it directly.
    '''
    CPIO_OUT_DIR = "cpio-root"
    CPIO_HEADER_SIZE = 110

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
        out_dir_base_name = os.path.join(os.path.dirname(fname), self.CPIO_OUT_DIR)
        out_dir = binwalk.core.common.unique_file_name(out_dir_base_name)

        try:
            fpin = open(fname, "rb")
            fperr = open(os.devnull, "rb")
            os.mkdir(out_dir)
        except OSError:
            return False

        try:
            curdir = os.getcwd()
            os.chdir(out_dir)
        except OSError:
            return False

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
        self.consecutive_hits = 0

    def new_file(self, f):
        # Make sure internal settings don't persist across different files
        self.pre_scan()

    def _get_file_name(self, description):
        name = ''
        if 'file name: "' in description:
            name = description.split('file name: "')[1].split('"')[0]
        return name

    def _get_file_name_length(self, description):
        length = None
        if 'file name length: "' in description:
            length_string = description.split('file name length: "')[1].split('"')[0]
            try:
                length = int(length_string, 0)
            except ValueError:
                pass
        return length

    def _get_file_size(self, description):
        size = None
        if 'file size: "' in description:
            size_string = description.split('file size: "')[1].split('"')[0]
            try:
                size = int(size_string, 0)
            except ValueError:
                pass
        return size

    def scan(self, result):
        if result.valid:
            # ASCII CPIO archives consist of multiple entries, ending with an entry named 'TRAILER!!!'.
            # Displaying each entry is useful, as it shows what files are contained in the archive,
            # but we only want to extract the archive when the first entry is
            # found.
            if result.description.startswith('ASCII cpio archive'):

                # Parse the reported name length and file size
                file_size = self._get_file_size(result.description)
                file_name = self._get_file_name(result.description)
                file_name_length = self._get_file_name_length(result.description)

                # The +1 is to include the terminating NULL byte
                if None in [file_size, file_name_length] or file_name_length != len(file_name)+1:
                    # If the reported length of the file name doesn't match the actual
                    # file name length, treat this as a false positive result.
                    result.valid = False
                    return

                # Instruct binwalk to skip the rest of this CPIO entry.
                # We don't want/need to scan what's inside it.
                result.jump = self.CPIO_HEADER_SIZE + file_size + file_name_length
                self.consecutive_hits += 1

                if not self.found_archive or self.found_archive_in_file != result.file.path:
                    # This is the first entry. Set found_archive and allow the
                    # scan to continue normally.
                    self.found_archive_in_file = result.file.path
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
                # TODO: It would be better to jump to the end of this CPIO
                # entry rather than make this assumption...
                result.valid = False

