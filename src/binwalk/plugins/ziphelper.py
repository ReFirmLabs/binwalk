import binwalk.core.plugin

class ZipHelperPlugin(binwalk.core.plugin.Plugin):
    '''
    A helper plugin for Zip files to ensure that the Zip archive
    extraction rule is only executed once when the first Zip archive
    entry is encountered. This resets once and end of zip archive is
    found.
    '''
    MODULES = ['Signature']

    extraction_active = False

    def scan(self, result):
        if result.valid and result.display:
            if result.description.lower().startswith('zip archive data'):
                if self.extraction_active:
                    result.extract = False
                else:
                    self.extraction_active = True
            elif result.description.lower().startswith('end of zip archive'):
                self.extraction_active = False
