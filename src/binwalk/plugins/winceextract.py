import binwalk.core.plugin
import re
import os

from binwalk.plugins.winceextractor import WinCEExtractor

class WinceExtract(binwalk.core.plugin.Plugin):

    MODULES = ['Signature']

    ROM_DESCRIPTION_RE  = re.compile(r"^windows ce memory segment header, toc address: 0x([0-9a-fA-F]+)$", re.IGNORECASE)
    SEGMENT_NAMES       = [".text", ".data", ".pdata", ".rsrc", ".other"]

    def init(self):
        """
        Initializes this plugin for binwalk. Adds an extractor rule for a
        Windows CE ROM file.

        :return: None
        """
        if self.module.extractor.enabled:
            self.module.extractor.add_rule(txtrule=None,
                                           regex=WinceExtract.ROM_DESCRIPTION_RE.pattern,
                                           extension="bin",
                                           recurse=False,
                                           cmd=self.extractor)

        self.image_start = None
            
    def scan(self, result):
        """
        Called everytime binwalk finds a signature in a file. If the signature
        is a Windows CE ROM header, the offset will be saved.

        :param result: a signature result from a file

        :return: None
        """
        if self.image_start is None:
            match = WinceExtract.ROM_DESCRIPTION_RE.match(result.description)
            if match is not None:
                self.image_start = result.offset

    def extractor(self, fname):
        """
        Called when a file matches the extraction criteria set by the init method.
        This should be called after the scan has been called for a Windows CE ROM header.
        
        Reads and extracts files from a Windows CE ROM file.

        :param fname: the filename of Windows CE ROM file

        :return: None
        """
        infile      = os.path.abspath(fname)
        indir       = os.path.dirname(infile)

        with open(infile, 'r+b') as f:
            with WinCEExtractor(f, 0) as extractor:
                for module in extractor.modules:
                    with open(os.path.join(indir, module.file_name), 'w+b') as module_file:
                        module.write_to(module_file)
                for file_e in extractor.files:
                    with open(os.path.join(indir, file_e.file_name), 'w+b') as file_file:
                        file_e.write_to(file_file)
