# Performs extraction of data that matches extraction rules.
# This is automatically invoked by core.module code if extraction has been
# enabled by the user; other modules need not reference this module directly.

import os
import re
import sys
import stat
import shlex
import tempfile
import subprocess
import binwalk.core.common
from binwalk.core.compat import *
from binwalk.core.module import Module, Option, Kwarg
from binwalk.core.common import file_size, file_md5, unique_file_name, BlockFile

class ExtractInfo(object):
    def __init__(self):
        self.carved = {}
        self.extracted = {}
        self.directory = None

class Extractor(Module):
    '''
    Extractor class, responsible for extracting files from the target file and executing external applications, if requested.
    '''
    # Extract rules are delimited with a colon.
    # <case insensitive matching string>:<file extension>[:<command to run>]
    RULE_DELIM = ':'

    # Comments in the extract.conf files start with a pound
    COMMENT_DELIM ='#'

    # Place holder for the extracted file name in the command
    FILE_NAME_PLACEHOLDER = '%e'

    # Unique path delimiter, used for generating unique output file/directory names.
    # Useful when, for example, extracting two squashfs images (squashfs-root, squashfs-root-0).
    UNIQUE_PATH_DELIMITER = '%%'

    TITLE = 'Extraction'
    ORDER = 9
    PRIMARY = False

    CLI = [
            Option(short='e',
                   long='extract',
                   kwargs={'load_default_rules' : True, 'enabled' : True},
                   description='Automatically extract known file types'),
            Option(short='D',
                   long='dd',
                   type=list,
                   dtype='type:ext:cmd',
                   kwargs={'manual_rules' : [], 'enabled' : True},
                   description='Extract <type> signatures, give the files an extension of <ext>, and execute <cmd>'),
            Option(short='M',
                   long='matryoshka',
                   kwargs={'matryoshka' : 8},
                   description='Recursively scan extracted files'),
            Option(short='d',
                   long='depth',
                   type=int,
                   kwargs={'matryoshka' : 0},
                   description='Limit matryoshka recursion depth (default: 8 levels deep)'),
            Option(short='C',
                   long='directory',
                   type=str,
                   kwargs={'base_directory' : 0},
                   description='Extract files/folders to a custom directory (default: current working directory)'),
            Option(short='j',
                   long='size',
                   type=int,
                   kwargs={'max_size' : 0},
                   description='Limit the size of each extracted file'),
            Option(short='r',
                   long='rm',
                   kwargs={'remove_after_execute' : True},
                   description='Delete carved files after extraction'),
            Option(short='z',
                   long='carve',
                   kwargs={'run_extractors' : False},
                   description="Carve data from files, but don't execute extraction utilities"),
    ]

    KWARGS = [
            Kwarg(name='max_size', default=None),
            Kwarg(name='base_directory', default=None),
            Kwarg(name='remove_after_execute', default=False),
            Kwarg(name='load_default_rules', default=False),
            Kwarg(name='run_extractors', default=True),
            Kwarg(name='manual_rules', default=[]),
            Kwarg(name='matryoshka', default=0),
            Kwarg(name='enabled', default=False),
    ]

    def load(self):
        # Holds a list of extraction rules loaded either from a file or when manually specified.
        self.extract_rules = []
        # The input file specific output directory path (to be determined at runtime)
        self.directory = None
        # Key value pairs of input file path and output extraction path
        self.output = {}

        if self.load_default_rules:
            self.load_defaults()

        for manual_rule in self.manual_rules:
            self.add_rule(manual_rule)

        if self.matryoshka:
            self.config.verbose = True

    def add_pending(self, f):
        # Ignore symlinks
        if os.path.islink(f):
            return

        # Get the file mode to check and see if it's a block/char device
        try:
            file_mode = os.stat(f).st_mode
        except OSError as e:
            return

        # Only add this to the pending list of files to scan
        # if the file is a regular file or a block/character device.
        if (stat.S_ISREG(file_mode) or
            stat.S_ISBLK(file_mode) or
            stat.S_ISCHR(file_mode)):
            self.pending.append(f)

    def reset(self):
        # Holds a list of pending files that should be scanned; only populated if self.matryoshka == True
        self.pending = []
        # Holds a dictionary of extraction directories created for each scanned file.
        self.extraction_directories = {}
        # Holds a dictionary of the last directory listing for a given directory; used for identifying
        # newly created/extracted files that need to be appended to self.pending.
        self.last_directory_listing = {}

    def callback(self, r):
        # Make sure the file attribute is set to a compatible instance of binwalk.core.common.BlockFile
        try:
            r.file.size
        except KeyboardInterrupt as e:
            pass
        except Exception as e:
            return

        if not r.size:
            size = r.file.size - r.offset
        else:
            size = r.size

        # Only extract valid results that have been marked for extraction and displayed to the user.
        # Note that r.display is still True even if --quiet has been specified; it is False if the result has been
        # explicitly excluded via the -y/-x options.
        if r.valid and r.extract and r.display:
            # Create some extract output for this file, it it doesn't already exist
            if not binwalk.core.common.has_key(self.output, r.file.path):
                self.output[r.file.path] = ExtractInfo()

            # Attempt extraction
            binwalk.core.common.debug("Extractor callback for %s @%d [%s]" % (r.file.name, r.offset, r.description))
            (extraction_directory, dd_file, scan_extracted_files) = self.extract(r.offset, r.description, r.file.path, size, r.name)

            # If the extraction was successful, self.extract will have returned the output directory and name of the dd'd file
            if extraction_directory and dd_file:
                # Get the full path to the dd'd file and save it in the output info for this file
                dd_file_path = os.path.join(extraction_directory, dd_file)
                self.output[r.file.path].carved[r.offset] = dd_file_path
                self.output[r.file.path].extracted[r.offset] = []

                # Do a directory listing of the output directory
                directory_listing = set(os.listdir(extraction_directory))

                # If this is a newly created output directory, self.last_directory_listing won't have a record of it.
                # If we've extracted other files to this directory before, it will.
                if not has_key(self.last_directory_listing, extraction_directory):
                    self.last_directory_listing[extraction_directory] = set()

                # Loop through a list of newly created files (i.e., files that weren't listed in the last directory listing)
                for f in directory_listing.difference(self.last_directory_listing[extraction_directory]):
                    # Build the full file path and add it to the extractor results
                    file_path = os.path.join(extraction_directory, f)
                    real_file_path = os.path.realpath(file_path)
                    self.result(description=file_path, display=False)

                    # Also keep a list of files created by the extraction utility
                    if real_file_path != dd_file_path:
                        self.output[r.file.path].extracted[r.offset].append(real_file_path)

                    # If recursion was specified, and the file is not the same one we just dd'd
                    if (self.matryoshka and
                        file_path != dd_file_path and
                        scan_extracted_files and
                        self.directory in real_file_path):
                        # If the recursion level of this file is less than or equal to our desired recursion level
                        if len(real_file_path.split(self.directory)[1].split(os.path.sep)) <= self.matryoshka:
                            # If this is a directory and we are supposed to process directories for this extractor,
                            # then add all files under that directory to the list of pending files.
                            if os.path.isdir(file_path):
                                for root, dirs, files in os.walk(file_path):
                                    for f in files:
                                        full_path = os.path.join(root, f)
                                        self.add_pending(full_path)
                            # If it's just a file, it to the list of pending files
                            else:
                                self.add_pending(file_path)

                # Update the last directory listing for the next time we extract a file to this same output directory
                self.last_directory_listing[extraction_directory] = directory_listing

    def append_rule(self, r):
        self.extract_rules.append(r.copy())

    def add_rule(self, txtrule=None, regex=None, extension=None, cmd=None, codes=[0, None], recurse=True):
        '''
        Adds a set of rules to the extraction rule list.

        @txtrule   - Rule string, or list of rule strings, in the format <regular expression>:<file extension>[:<command to run>]
        @regex     - If rule string is not specified, this is the regular expression string to use.
        @extension - If rule string is not specified, this is the file extension to use.
        @cmd       - If rule string is not specified, this is the command to run.
                     Alternatively a callable object may be specified, which will be passed one argument: the path to the file to extract.
        @codes     - A list of valid return codes for the extractor.
        @recurse   - If False, extracted directories will not be recursed into when the matryoshka option is enabled.

        Returns None.
        '''
        rules = []
        match = False
        r = {
            'extension'     : '',
            'cmd'           : '',
            'regex'         : None,
            'codes'         : codes,
            'recurse'       : recurse,
        }

        # Process single explicitly specified rule
        if not txtrule and regex and extension:
            r['extension'] = extension
            r['regex'] = re.compile(regex)
            if cmd:
                r['cmd'] = cmd

            self.append_rule(r)
            return

        # Process rule string, or list of rule strings
        if not isinstance(txtrule, type([])):
            rules = [txtrule]
        else:
            rules = txtrule

        for rule in rules:
            r['cmd'] = ''
            r['extension'] = ''

            try:
                values = self._parse_rule(rule)
                match = values[0]
                r['regex'] = re.compile(values[0])
                r['extension'] = values[1]
                r['cmd'] = values[2]
                r['codes'] = values[3]
                r['recurse'] = values[4]
            except KeyboardInterrupt as e:
                raise e
            except Exception:
                pass

            # Verify that the match string was retrieved.
            if match:
                self.append_rule(r)

    def remove_rule(self, text):
        '''
        Remove all rules that match a specified text.

        @text - The text to match against.

        Returns the number of rules removed.
        '''
        rm = []

        for i in range(0, len(self.extract_rules)):
            if self.extract_rules[i]['regex'].match(text):
                rm.append(i)

        for i in rm:
            self.extract_rules.pop(i)

        return len(rm)

    def clear_rules(self):
        '''
        Deletes all extraction rules.

        Returns None.
        '''
        self.extract_rules = []

    def get_rules(self):
        '''
        Returns a list of all extraction rules.
        '''
        return self.extract_rules

    def load_from_file(self, fname):
        '''
        Loads extraction rules from the specified file.

        @fname - Path to the extraction rule file.

        Returns None.
        '''
        try:
            # Process each line from the extract file, ignoring comments
            with open(fname, 'r') as f:
                for rule in f.readlines():
                    self.add_rule(rule.split(self.COMMENT_DELIM, 1)[0])
        except KeyboardInterrupt as e:
            raise e
        except Exception as e:
            raise Exception("Extractor.load_from_file failed to load file '%s': %s" % (fname, str(e)))

    def load_defaults(self):
        '''
        Loads default extraction rules from the user and system extract.conf files.

        Returns None.
        '''
        # Load the user extract file first to ensure its rules take precedence.
        extract_files = [
            self.config.settings.user.extract,
            self.config.settings.system.extract,
        ]

        for extract_file in extract_files:
            if extract_file:
                try:
                    self.load_from_file(extract_file)
                except KeyboardInterrupt as e:
                    raise e
                except Exception as e:
                    if binwalk.core.common.DEBUG:
                        raise Exception("Extractor.load_defaults failed to load file '%s': %s" % (extract_file, str(e)))

    def build_output_directory(self, path):
        '''
        Set the output directory for extracted files.

        @path - The path to the file that data will be extracted from.

        Returns None.
        '''
        # If we have not already created an output directory for this target file, create one now
        if not has_key(self.extraction_directories, path):
            basedir = os.path.dirname(path)
            basename = os.path.basename(path)

            # Make sure we put the initial extracted file in the CWD
            if self.directory is None:
                if self.base_directory is None:
                    basedir = os.getcwd()
                else:
                    basedir = self.base_directory
                    if not os.path.exists(basedir):
                        os.mkdir(basedir)

            outdir = os.path.join(basedir, '_' + basename)
            output_directory = unique_file_name(outdir, extension='extracted')

            if not os.path.exists(output_directory):
                os.mkdir(output_directory)

            self.extraction_directories[path] = output_directory
        # Else, just use the already created directory
        else:
            output_directory = self.extraction_directories[path]

        # Set the initial base extraction directory for later determining the level of recusion
        if self.directory is None:
            self.directory = os.path.realpath(output_directory) + os.path.sep
            self.output[path].directory = self.directory

        return output_directory

    def cleanup_extracted_files(self, tf=None):
        '''
        Set the action to take after a file is extracted.

        @tf - If set to True, extracted files will be cleaned up after running a command against them.
              If set to False, extracted files will not be cleaned up after running a command against them.
              If set to None or not specified, the current setting will not be changed.

        Returns the current cleanup status (True/False).
        '''
        if tf is not None:
            self.remove_after_execute = tf

        return self.remove_after_execute

    def extract(self, offset, description, file_name, size, name=None):
        '''
        Extract an embedded file from the target file, if it matches an extract rule.
        Called automatically by Binwalk.scan().

        @offset      - Offset inside the target file to begin the extraction.
        @description - Description of the embedded file to extract, as returned by libmagic.
        @file_name   - Path to the target file.
        @size        - Number of bytes to extract.
        @name        - Name to save the file as.

        Returns the name of the extracted file (blank string if nothing was extracted).
        '''
        fname = ''
        original_dir = os.getcwd()
        rules = self.match(description)
        file_path = os.path.realpath(file_name)

        # No extraction rules for this file
        if not rules:
            return (None, None, False)
        else:
            binwalk.core.common.debug("Found %d matching extraction rules" % len(rules))

        output_directory = self.build_output_directory(file_name)

        # Extract to end of file if no size was specified
        if not size:
            size = file_size(file_path) - offset

        if os.path.isfile(file_path):
            os.chdir(output_directory)

            # Loop through each extraction rule until one succeeds
            for i in range(0, len(rules)):
                rule = rules[i]

                # Make sure we don't recurse into any extracted directories if instructed not to
                if rule['recurse'] in [True, False]:
                    recurse = rule['recurse']
                else:
                    recurse = True

                # Copy out the data to disk, if we haven't already
                fname = self._dd(file_path, offset, size, rule['extension'], output_file_name=name)

                # If there was a command specified for this rule, try to execute it.
                # If execution fails, the next rule will be attempted.
                if rule['cmd']:

                    # Note the hash of the original file; if --rm is specified and the
                    # extraction utility modifies the original file rather than creating
                    # a new one (AFAIK none currently do, but could happen in the future),
                    # we don't want to remove this file.
                    if self.remove_after_execute:
                        fname_md5 = file_md5(fname)

                    # Execute the specified command against the extracted file
                    if self.run_extractors:
                        extract_ok = self.execute(rule['cmd'], fname, rule['codes'])
                    else:
                        extract_ok = True

                    # Only clean up files if remove_after_execute was specified
                    if extract_ok == True and self.remove_after_execute:

                        # Remove the original file that we extracted,
                        # if it has not been modified by the extractor.
                        try:
                            if file_md5(fname) == fname_md5:
                                os.unlink(fname)
                        except KeyboardInterrupt as e:
                            raise e
                        except Exception as e:
                            pass

                    # If the command executed OK, don't try any more rules
                    if extract_ok == True:
                        break
                    # Else, remove the extracted file if this isn't the last rule in the list.
                    # If it is the last rule, leave the file on disk for the user to examine.
                    elif i != (len(rules)-1):
                        try:
                            os.unlink(fname)
                        except KeyboardInterrupt as e:
                            raise e
                        except Exception as e:
                            pass

                # If there was no command to execute, just use the first rule
                else:
                    break

            os.chdir(original_dir)

        return (output_directory, fname, recurse)

    def _entry_offset(self, index, entries, description):
        '''
        Gets the offset of the first entry that matches the description.

        @index       - Index into the entries list to begin searching.
        @entries     - Dictionary of result entries.
        @description - Case insensitive description.

        Returns the offset, if a matching description is found.
        Returns -1 if a matching description is not found.
        '''
        description = description.lower()

        for (offset, infos) in entries[index:]:
            for info in infos:
                if info['description'].lower().startswith(description):
                    return offset
        return -1

    def match(self, description):
        '''
        Check to see if the provided description string matches an extract rule.
        Called internally by self.extract().

        @description - Description string to check.

        Returns the associated rule dictionary if a match is found.
        Returns None if no match is found.
        '''
        rules = []
        description = description.lower()

        for rule in self.extract_rules:
            if rule['regex'].search(description):
                rules.append(rule)
        return rules

    def _parse_rule(self, rule):
        '''
        Parses an extraction rule.

        @rule - Rule string.

        Returns an array of ['<case insensitive matching string>', '<file extension>', '<command to run>', '<comma separated return codes>', <recurse into extracted directories: True|False>].
        '''
        values = rule.strip().split(self.RULE_DELIM, 4)

        if len(values) >= 4:
            codes = values[3].split(',')
            for i in range(0, len(codes)):
                try:
                    codes[i] = int(codes[i], 0)
                except ValueError as e:
                    binwalk.core.common.warning("The specified return code '%s' for extractor '%s' is not a valid number!" % (codes[i], values[0]))
            values[3] = codes

        if len(values) >= 5:
            values[4] = (values[4].lower() == 'true')

        return values

    def _dd(self, file_name, offset, size, extension, output_file_name=None):
        '''
        Extracts a file embedded inside the target file.

        @file_name        - Path to the target file.
        @offset           - Offset inside the target file where the embedded file begins.
        @size             - Number of bytes to extract.
        @extension        - The file exension to assign to the extracted file on disk.
        @output_file_name - The requested name of the output file.

        Returns the extracted file name.
        '''
        total_size = 0
        # Default extracted file name is <displayed hex offset>.<extension>
        default_bname = "%X" % (offset + self.config.base)

        if self.max_size and size > self.max_size:
            size = self.max_size

        if not output_file_name or output_file_name is None:
            bname = default_bname
        else:
            # Strip the output file name of invalid/dangerous characters (like file paths)
            bname = os.path.basename(output_file_name)

        fname = unique_file_name(bname, extension)

        try:
            # If byte swapping is enabled, we need to start reading at a swap-size
            # aligned offset, then index in to the read data appropriately.
            if self.config.swap_size:
                adjust = offset % self.config.swap_size
            else:
                adjust = 0

            offset -= adjust

            # Open the target file and seek to the offset
            fdin = self.config.open_file(file_name)
            fdin.seek(offset)

            # Open the output file
            try:
                fdout = BlockFile(fname, 'w')
            except KeyboardInterrupt as e:
                raise e
            except Exception as e:
                # Fall back to the default name if the requested name fails
                fname = unique_file_name(default_bname, extension)
                fdout = BlockFile(fname, 'w')

            while total_size < size:
                (data, dlen) = fdin.read_block()
                if not data:
                    break
                else:
                    fdout.write(str2bytes(data[adjust:dlen]))
                    total_size += (dlen-adjust)
                    adjust = 0

            # Cleanup
            fdout.close()
            fdin.close()
        except KeyboardInterrupt as e:
            raise e
        except Exception as e:
            raise Exception("Extractor.dd failed to extract data from '%s' to '%s': %s" % (file_name, fname, str(e)))

        binwalk.core.common.debug("Carved data block 0x%X - 0x%X from '%s' to '%s'" % (offset, offset+size, file_name, fname))
        return fname

    def execute(self, cmd, fname, codes=[0, None]):
        '''
        Execute a command against the specified file.

        @cmd   - Command to execute.
        @fname - File to run command against.
        @codes - List of return codes indicating cmd success.

        Returns True on success, False on failure, or None if the external extraction utility could not be found.
        '''
        tmp = None
        rval = 0
        retval = True

        binwalk.core.common.debug("Running extractor '%s'" % str(cmd))

        try:
            if callable(cmd):
                try:
                    retval = cmd(fname)
                except KeyboardInterrupt as e:
                    raise e
                except Exception as e:
                    binwalk.core.common.warning("Internal extractor '%s' failed with exception: '%s'" % (str(cmd), str(e)))
            elif cmd:
                # If not in debug mode, create a temporary file to redirect stdout and stderr to
                if not binwalk.core.common.DEBUG:
                    tmp = tempfile.TemporaryFile()

                # Execute.
                for command in cmd.split("&&"):

                    # Generate unique file paths for all paths in the current command that are surrounded by UNIQUE_PATH_DELIMITER
                    while self.UNIQUE_PATH_DELIMITER in command:
                        need_unique_path = command.split(self.UNIQUE_PATH_DELIMITER)[1].split(self.UNIQUE_PATH_DELIMITER)[0]
                        unique_path = binwalk.core.common.unique_file_name(need_unique_path)
                        command = command.replace(self.UNIQUE_PATH_DELIMITER + need_unique_path + self.UNIQUE_PATH_DELIMITER, unique_path)

                    # Replace all instances of FILE_NAME_PLACEHOLDER in the command with fname
                    command = command.strip().replace(self.FILE_NAME_PLACEHOLDER, fname)

                    binwalk.core.common.debug("subprocess.call(%s, stdout=%s, stderr=%s)" % (command, str(tmp), str(tmp)))
                    rval = subprocess.call(shlex.split(command), stdout=tmp, stderr=tmp)

                    if rval in codes:
                        retval = True
                    else:
                        retval = False

                    binwalk.core.common.debug('External extractor command "%s" completed with return code %d (success: %s)' % (cmd, rval, str(retval)))

                    # TODO: Should errors from all commands in a command string be checked? Currently we only support
                    #       specifying one set of error codes, so at the moment, this is not done; it is up to the
                    #       final command to return success or failure (which presumably it will if previous necessary
                    #       commands were not successful, but this is an assumption).
                    #if retval == False:
                    #    break

        except KeyboardInterrupt as e:
            raise e
        except Exception as e:
            binwalk.core.common.warning("Extractor.execute failed to run external extractor '%s': %s" % (str(cmd), str(e)))
            retval = None

        if tmp is not None:
            tmp.close()

        return retval


