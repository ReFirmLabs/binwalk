# Performs fuzzy hashing against files/directories.
# Unlike other scans, this doesn't produce any file offsets, so its results are not applicable to 
# some other scans, such as the entropy scan.
# Additionally, this module currently doesn't support certian general options (length, offset, swap, etc),
# as the libfuzzy C library is responsible for opening and scanning the specified files.

import os
import re
import ctypes
import fnmatch
import binwalk.core.C
import binwalk.core.common
from binwalk.core.compat import *
from binwalk.core.module import Module, Option, Kwarg

class HashResult(object):
    '''
    Class for storing libfuzzy hash results.
    For internal use only.
    '''

    def __init__(self, name, hash=None, strings=None):
        self.name = name
        self.hash = hash
        self.strings = strings

class HashMatch(Module):
    '''
    Class for fuzzy hash matching of files and directories.
    '''
    DEFAULT_CUTOFF = 0
    CONSERVATIVE_CUTOFF = 90

    TITLE = "Fuzzy Hash"

    CLI = [
        Option(short='F',
               long='fuzzy',
               kwargs={'enabled' : True},
               description='Perform fuzzy hash matching on files/directories'),
        Option(short='u',
               long='cutoff',
               priority=100,
               type=int,
               kwargs={'cutoff' : DEFAULT_CUTOFF},
               description='Set the cutoff percentage'),
        Option(short='S',
               long='strings',
               kwargs={'strings' : True},
               description='Diff strings inside files instead of the entire file'),
        Option(short='s',
               long='same',
               kwargs={'same' : True, 'cutoff' : CONSERVATIVE_CUTOFF},
               description='Only show files that are the same'),
        Option(short='p',
               long='diff',
               kwargs={'same' : False, 'cutoff' : CONSERVATIVE_CUTOFF},
               description='Only show files that are different'),
        Option(short='n',
               long='name',
               kwargs={'filter_by_name' : True},
               description='Only compare files whose base names are the same'),
        Option(short='L',
               long='symlinks',
               kwargs={'symlinks' : True},
               description="Don't ignore symlinks"),
    ]

    KWARGS = [
        Kwarg(name='cutoff', default=DEFAULT_CUTOFF),
        Kwarg(name='strings', default=False),
        Kwarg(name='same', default=True),
        Kwarg(name='symlinks', default=False),
        Kwarg(name='max_results', default=None),
        Kwarg(name='abspath', default=False),
        Kwarg(name='filter_by_name', default=False),
        Kwarg(name='symlinks', default=False),
        Kwarg(name='enabled', default=False),
    ]

    LIBRARY_NAME = "fuzzy"
    LIBRARY_FUNCTIONS = [
            binwalk.core.C.Function(name="fuzzy_hash_buf", type=int),
            binwalk.core.C.Function(name="fuzzy_hash_filename", type=int),
            binwalk.core.C.Function(name="fuzzy_compare", type=int),
    ]

    # Max result is 148 (http://ssdeep.sourceforge.net/api/html/fuzzy_8h.html)
    FUZZY_MAX_RESULT = 150
    # Files smaller than this won't produce meaningful fuzzy results (from ssdeep.h)
    FUZZY_MIN_FILE_SIZE = 4096

    HEADER_FORMAT = "\n%s" + " " * 11 + "%s\n" 
    RESULT_FORMAT = "%d%%" + " " * 17 + "%s\n"
    HEADER = ["SIMILARITY", "FILE NAME"]
    RESULT = ["percentage", "description"]

    def init(self):
        self.total = 0
        self.last_file1 = HashResult(None)
        self.last_file2 = HashResult(None)

        self.lib = binwalk.core.C.Library(self.LIBRARY_NAME, self.LIBRARY_FUNCTIONS)

    def _get_strings(self, fname):
        return ''.join(list(binwalk.core.common.strings(fname, minimum=10)))

    def _show_result(self, match, fname):
        if self.abspath:
            fname = os.path.abspath(fname)

        # Add description string padding for alignment
        if match < 100:
            fname = ' ' + fname
        if match < 10:
            fname = ' ' + fname

        self.result(percentage=match, description=fname, plot=False)

    def _compare_files(self, file1, file2):
        '''
        Fuzzy diff two files.
            
        @file1 - The first file to diff.
        @file2 - The second file to diff.
    
        Returns the match percentage.    
        Returns None on error.
        '''
        status = 0
        file1_dup = False
        file2_dup = False

        if not self.filter_by_name or os.path.basename(file1) == os.path.basename(file2):
            if os.path.exists(file1) and os.path.exists(file2):

                hash1 = ctypes.create_string_buffer(self.FUZZY_MAX_RESULT)
                hash2 = ctypes.create_string_buffer(self.FUZZY_MAX_RESULT)

                # Check if the last file1 or file2 matches this file1 or file2; no need to re-hash if they match.
                if file1 == self.last_file1.name and self.last_file1.hash:
                    file1_dup = True
                else:
                    self.last_file1.name = file1

                if file2 == self.last_file2.name and self.last_file2.hash:
                    file2_dup = True
                else:
                    self.last_file2.name = file2

                try:
                    if self.strings:
                        if file1_dup:
                            file1_strings = self.last_file1.strings
                        else:
                            self.last_file1.strings = file1_strings = self._get_strings(file1)
                            
                        if file2_dup:
                            file2_strings = self.last_file2.strings
                        else:
                            self.last_file2.strings = file2_strings = self._get_strings(file2)

                        if file1_strings == file2_strings:
                            return 100
                        else:
                            if file1_dup:
                                hash1 = self.last_file1.hash
                            else:
                                status |= self.lib.fuzzy_hash_buf(file1_strings, len(file1_strings), hash1)

                            if file2_dup:
                                hash2 = self.last_file2.hash
                            else:
                                status |= self.lib.fuzzy_hash_buf(file2_strings, len(file2_strings), hash2)
                        
                    else:
                        if file1_dup:
                            hash1 = self.last_file1.hash
                        else:
                            status |= self.lib.fuzzy_hash_filename(file1, hash1)
                            
                        if file2_dup:
                            hash2 = self.last_file2.hash
                        else:
                            status |= self.lib.fuzzy_hash_filename(file2, hash2)
                
                    if status == 0:
                        if not file1_dup:
                            self.last_file1.hash = hash1
                        if not file2_dup:
                            self.last_file2.hash = hash2

                        if hash1.raw == hash2.raw:
                            return 100
                        else:
                            return self.lib.fuzzy_compare(hash1, hash2)
                except Exception as e:
                    binwalk.core.common.warning("Exception while doing fuzzy hash: %s" % str(e))

        return None

    def is_match(self, match):
        '''
        Returns True if this is a good match.
        Returns False if his is not a good match.
        '''
        return (match is not None and ((match >= self.cutoff and self.same) or (match < self.cutoff and not self.same)))

    def _get_file_list(self, directory):
        '''
        Generates a directory tree.

        @directory - The root directory to start from.

        Returns a set of file paths, excluding the root directory.
        '''
        file_list = []

        # Normalize directory path so that we can exclude it from each individual file path
        directory = os.path.abspath(directory) + os.path.sep

        for (root, dirs, files) in os.walk(directory):
            # Don't include the root directory in the file paths
            root = ''.join(root.split(directory, 1)[1:])

            # Get a list of files, with or without symlinks as specified during __init__
            files = [os.path.join(root, f) for f in files if self.symlinks or not os.path.islink(f)]

            file_list += files
            
        return set(file_list)

    def hash_files(self, needle, haystack):
        '''
        Compare one file against a list of other files.
        
        Returns a list of tuple results.
        '''
        self.total = 0

        for f in haystack:
            m = self._compare_files(needle, f)
            if m is not None and self.is_match(m):
                self._show_result(m, f)
                    
                self.total += 1
                if self.max_results and self.total >= self.max_results:
                    break

    def hash_file(self, needle, haystack):
        '''
        Search for one file inside one or more directories.

        Returns a list of tuple results.
        '''
        matching_files = []
        self.total = 0
        done = False

        for directory in haystack:
            for f in self._get_file_list(directory):
                f = os.path.join(directory, f)
                m = self._compare_files(needle, f)
                if m is not None and self.is_match(m):
                    self._show_result(m, f)
                    matching_files.append((m, f))
                    
                    self.total += 1
                    if self.max_results and self.total >= self.max_results:
                        done = True
                        break
            if done:
                break
                    
        return matching_files

    def hash_directories(self, needle, haystack):
        '''
        Compare the contents of one directory with the contents of other directories.

        Returns a list of tuple results.
        '''
        done = False
        self.total = 0

        source_files = self._get_file_list(needle)

        for directory in haystack:
            dir_files = self._get_file_list(directory)

            for source_file in source_files:
                for dir_file in dir_files:
                    file1 = os.path.join(needle, source_file)
                    file2 = os.path.join(directory, dir_file)

                    m = self._compare_files(file1, file2)
                    if m is not None and self.is_match(m):
                        self._show_result(m, "%s => %s" % (file1, file2))

                        self.total += 1
                        if self.max_results and self.total >= self.max_results:
                            done = True
                            break
            if done:
                break

    def run(self):
        '''
        Main module method.
        '''
        # Access the raw self.config.files list directly here, since we accept both
        # files and directories and self.next_file only works for files.
        needle = self.config.files[0]
        haystack = self.config.files[1:]

        self.header()
                
        if os.path.isfile(needle):
            if os.path.isfile(haystack[0]):
                self.hash_files(needle, haystack)
            else:
                self.hash_file(needle, haystack)
        else:
            self.hash_directories(needle, haystack)

        self.footer()

        return True
