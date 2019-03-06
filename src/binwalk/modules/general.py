# Module to process general user input options (scan length, starting
# offset, etc).

import io
import os
import re
import sys
import argparse
import binwalk.core.idb
import binwalk.core.common
import binwalk.core.display
import binwalk.core.settings
from binwalk.core.compat import *
from binwalk.core.module import Module, Option, Kwarg, show_help


class General(Module):

    TITLE = "General"
    ORDER = 0

    DEFAULT_DEPENDS = []

    CLI = [
        Option(long='length',
               short='l',
               type=int,
               kwargs={'length': 0},
               description='Number of bytes to scan'),
        Option(long='offset',
               short='o',
               type=int,
               kwargs={'offset': 0},
               description='Start scan at this file offset'),
        Option(long='base',
               short='O',
               type=int,
               kwargs={'base': 0},
               description='Add a base address to all printed offsets'),
        Option(long='block',
               short='K',
               type=int,
               kwargs={'block': 0},
               description='Set file block size'),
        Option(long='swap',
               short='g',
               type=int,
               kwargs={'swap_size': 0},
               description='Reverse every n bytes before scanning'),
        Option(long='log',
               short='f',
               type=argparse.FileType,
               kwargs={'log_file': None},
               description='Log results to file'),
        Option(long='csv',
               short='c',
               kwargs={'csv': True},
               description='Log results to file in CSV format'),
        Option(long='term',
               short='t',
               kwargs={'format_to_terminal': True},
               description='Format output to fit the terminal window'),
        Option(long='quiet',
               short='q',
               kwargs={'quiet': True},
               description='Suppress output to stdout'),
        Option(long='verbose',
               short='v',
               kwargs={'verbose': True},
               description='Enable verbose output'),
        Option(short='h',
               long='help',
               kwargs={'show_help': True},
               description='Show help output'),
        Option(short='a',
               long='finclude',
               type=str,
               kwargs={'file_name_include_regex': ""},
               description='Only scan files whose names match this regex'),
        Option(short='p',
               long='fexclude',
               type=str,
               kwargs={'file_name_exclude_regex': ""},
               description='Do not scan files whose names match this regex'),
        Option(short='s',
               long='status',
               type=int,
               kwargs={'status_server_port': 0},
               description='Enable the status server on the specified port'),
        Option(long=None,
               short=None,
               type=binwalk.core.common.BlockFile,
               kwargs={'files': []}),

        # Hidden, API-only arguments
        Option(long="string",
               hidden=True,
               kwargs={'subclass': binwalk.core.common.StringFile}),
    ]

    KWARGS = [
        Kwarg(name='length', default=0),
        Kwarg(name='offset', default=0),
        Kwarg(name='base', default=0),
        Kwarg(name='block', default=0),
        Kwarg(name='status_server_port', default=0),
        Kwarg(name='swap_size', default=0),
        Kwarg(name='log_file', default=None),
        Kwarg(name='csv', default=False),
        Kwarg(name='format_to_terminal', default=False),
        Kwarg(name='quiet', default=False),
        Kwarg(name='verbose', default=False),
        Kwarg(name='files', default=[]),
        Kwarg(name='show_help', default=False),
        Kwarg(name='keep_going', default=False),
        Kwarg(name='subclass', default=io.FileIO),
        Kwarg(name='file_name_include_regex', default=None),
        Kwarg(name='file_name_exclude_regex', default=None),
    ]

    PRIMARY = False

    def load(self):
        self.threads_active = False
        self.target_files = []

        # A special case for when we're loaded into IDA
        if self.subclass == io.FileIO and binwalk.core.idb.LOADED_IN_IDA:
            self.subclass = binwalk.core.idb.IDBFileIO

        # Order is important with these two methods
        self._open_target_files()
        self._set_verbosity()

        # Build file name filter regex rules
        if self.file_name_include_regex:
            self.file_name_include_regex = re.compile(self.file_name_include_regex)
        if self.file_name_exclude_regex:
            self.file_name_exclude_regex = re.compile(self.file_name_exclude_regex)

        self.settings = binwalk.core.settings.Settings()
        self.display = binwalk.core.display.Display(log=self.log_file,
                                                    csv=self.csv,
                                                    quiet=self.quiet,
                                                    verbose=self.verbose,
                                                    fit_to_screen=self.format_to_terminal)

        if self.show_help:
            show_help()
            if not binwalk.core.idb.LOADED_IN_IDA:
                sys.exit(0)

        if self.status_server_port > 0:
            self.parent.status_server(self.status_server_port)

    def reset(self):
        pass

    def _set_verbosity(self):
        '''
        Sets the appropriate verbosity.
        Must be called after self._test_target_files so that self.target_files is properly set.
        '''
        # If more than one target file was specified, enable verbose mode; else, there is
        # nothing in some outputs to indicate which scan corresponds to which
        # file.
        if len(self.target_files) > 1 and not self.verbose:
            self.verbose = True

    def file_name_filter(self, fp):
        '''
        Checks to see if a file should be scanned based on file name include/exclude filters.
        Most useful for matryoshka scans where only certian files are desired.

        @fp - An instances of binwalk.common.BlockFile

        Returns True if the file should be scanned, False if not.
        '''
        if self.file_name_include_regex and not self.file_name_include_regex.search(fp.name):
            return False
        if self.file_name_exclude_regex and self.file_name_exclude_regex.search(fp.name):
            return False

        return True

    def open_file(self, fname, length=None, offset=None, swap=None, block=None, peek=None):
        '''
        Opens the specified file with all pertinent configuration settings.
        '''
        if length is None:
            length = self.length
        if offset is None:
            offset = self.offset
        if swap is None:
            swap = self.swap_size

        return binwalk.core.common.BlockFile(fname,
                                             subclass=self.subclass,
                                             length=length,
                                             offset=offset,
                                             swap=swap,
                                             block=block,
                                             peek=peek)

    def _open_target_files(self):
        '''
        Checks if the target files can be opened.
        Any files that cannot be opened are removed from the self.target_files list.
        '''
        # Validate the target files listed in target_files
        for tfile in self.files:
            # Ignore directories.
            if not self.subclass == io.FileIO or not os.path.isdir(tfile):
                # Make sure we can open the target files
                try:
                    fp = self.open_file(tfile)
                    fp.close()
                    self.target_files.append(tfile)
                except KeyboardInterrupt as e:
                    raise e
                except Exception as e:
                    self.error(description="Cannot open file %s (CWD: %s) : %s" % (tfile, os.getcwd(), str(e)))
