import binwalk.core.plugin

class CPIOPlugin(binwalk.core.plugin.Plugin):
    '''
    Ensures that ASCII CPIO archive entries only get extracted once.    
    '''

    MODULES = ['Signature']

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
                if not self.found_archive or self.found_archive_in_file != result.file.name:
                    # This is the first entry. Set found_archive and allow the scan to continue normally.
                    self.found_archive_in_file = result.file.name
                    self.found_archive = True
                    result.extract = True
                elif 'TRAILER!!!' in result.description:
                    # This is the last entry, un-set found_archive.
                    self.found_archive = False
                    result.extract = False
                else:
                    # The first entry has already been found and this is not the last entry, or the last entry 
                    # has not yet been found. Don't extract.
                    result.extract = False
            else:
                # If this was a valid non-CPIO archive result, reset these values; else, a previous
                # false positive CPIO result could leave these set, causing a subsequent valid CPIO
                # result to not be extracted.
                self.found_archive = False
                self.found_archive_in_file = None
