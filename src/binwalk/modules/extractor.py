# Performs extraction of data that matches extraction rules.
# This is automatically invoked by core.module code if extraction has been
# enabled by the user; other modules need not reference this module directly.

import os
import re
import stat
import shlex
import tempfile
import subprocess
import binwalk.core.common
from binwalk.core.compat import *
from binwalk.core.module import Module, Option, Kwarg
from binwalk.core.common import file_size, file_md5, unique_file_name, BlockFile


class ExtractDetails(object):
    def __init__(self, **kwargs):
        for (k, v) in iterator(kwargs):
            setattr(self, k, v)


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
    COMMENT_DELIM = '#'

    # Place holder for the extracted file name in the command
    FILE_NAME_PLACEHOLDER = '%e'

    # Unique path delimiter, used for generating unique output file/directory names.
    # Useful when, for example, extracting two squashfs images (squashfs-root,
    # squashfs-root-0).
    UNIQUE_PATH_DELIMITER = '%%'

    TITLE = 'Extraction'
    ORDER = 9
    PRIMARY = False

    CLI = [
        Option(short='e',
               long='extract',
               kwargs={'load_default_rules': True, 'enabled': True},
               description='Automatically extract known file types'),
        Option(short='D',
               long='dd',
               type=list,
               dtype='type[:ext[:cmd]]',
               kwargs={'manual_rules': [], 'enabled': True},
               description='Extract <type> signatures (regular expression), give the files an extension of <ext>, '
                           'and execute <cmd>'),
        Option(short='M',
               long='matryoshka',
               kwargs={'matryoshka': 8},
               description='Recursively scan extracted files'),
        Option(short='d',
               long='depth',
               type=int,
               kwargs={'matryoshka': 0},
               description='Limit matryoshka recursion depth (default: 8 levels deep)'),
        Option(short='C',
               long='directory',
               type=str,
               kwargs={'base_directory': 0},
               description='Extract files/folders to a custom directory (default: current working directory)'),
        Option(short='j',
               long='size',
               type=int,
               kwargs={'max_size': 0},
               description='Limit the size of each extracted file'),
        Option(short='n',
               long='count',
               type=int,
               kwargs={'max_count': 0},
               description='Limit the number of extracted files'),
        #Option(short='u',
        #       long='limit',
        #       type=int,
        #       kwargs={'recursive_max_size': 0},
        #       description="Limit the total size of all extracted files"),
        Option(short='r',
               long='rm',
               kwargs={'remove_after_execute': True},
               description='Delete carved files after extraction'),
        Option(short='z',
               long='carve',
               kwargs={'run_extractors': False},
               description="Carve data from files, but don't execute extraction utilities"),
        Option(short='V',
               long='subdirs',
               kwargs={'extract_into_subdirs': True},
               description="Extract into sub-directories named by the offset"),
    ]

    KWARGS = [
        Kwarg(name='max_size', default=None),
        Kwarg(name='recursive_max_size', default=None),
        Kwarg(name='max_count', default=None),
        Kwarg(name='base_directory', default=None),
        Kwarg(name='remove_after_execute', default=False),
        Kwarg(name='load_default_rules', default=False),
        Kwarg(name='run_extractors', default=True),
        Kwarg(name='extract_into_subdirs', default=False),
        Kwarg(name='manual_rules', default=[]),
        Kwarg(name='matryoshka', default=0),
        Kwarg(name='enabled', default=False),
    ]

    def load(self):
        # Holds a list of extraction rules loaded either from a file or when
        # manually specified.
        self.extract_rules = []
        # The input file specific output directory path (default to CWD)
        if self.base_directory:
            self.directory = os.path.realpath(self.base_directory)
            if not os.path.exists(self.directory):
                os.makedirs(self.directory)
        else:
            self.directory = os.getcwd()
        # Key value pairs of input file path and output extraction path
        self.output = {}
        # Number of extracted files
        self.extraction_count = 0
        # Override the directory name used for extraction output directories
        self.output_directory_override = None

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
        # if the file is a regular file. Special files (block/character
        # devices) can be tricky; they may fail to open, or worse, simply
        # hang when an attempt to open them is made. So for recursive
        # extraction purposes, they are ignored, albeit with a warning to
        # the user.
        if stat.S_ISREG(file_mode):
            # Make sure we can open the file too...
            try:
                fp = binwalk.core.common.BlockFile(f)
                fp.close()
                self.pending.append(f)
            except IOError as e:
                binwalk.core.common.warning("Ignoring file '%s': %s" % (f, str(e)))
        else:
            binwalk.core.common.warning("Ignoring file '%s': Not a regular file" % f)

    def reset(self):
        # Holds a list of pending files that should be scanned; only populated
        # if self.matryoshka == True
        self.pending = []
        # Holds a dictionary of extraction directories created for each scanned
        # file.
        self.extraction_directories = {}
        # Holds a dictionary of the last directory listing for a given directory; used for identifying
        # newly created/extracted files that need to be appended to
        # self.pending.
        self.last_directory_listing = {}

    def callback(self, r):
        # Make sure the file attribute is set to a compatible instance of
        # binwalk.core.common.BlockFile
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
        if r.valid and r.extract and r.display and (not self.max_count or self.extraction_count < self.max_count):
            # Create some extract output for this file, it it doesn't already
            # exist
            if not binwalk.core.common.has_key(self.output, r.file.path):
                self.output[r.file.path] = ExtractInfo()

            # Attempt extraction
            binwalk.core.common.debug("Extractor callback for %s @%d [%s]" % (r.file.name,
                                                                              r.offset,
                                                                              r.description))
            (extraction_directory, dd_file, scan_extracted_files, extraction_utility) = self.extract(r.offset,
                                                                                                     r.description,
                                                                                                     r.file.path,
                                                                                                     size,
                                                                                                     r.name)

            # If the extraction was successful, self.extract will have returned
            # the output directory and name of the dd'd file
            if extraction_directory and dd_file:
                # Track the number of extracted files
                self.extraction_count += 1

                # Get the full path to the dd'd file and save it in the output
                # info for this file
                dd_file_path = os.path.join(extraction_directory, dd_file)
                self.output[r.file.path].carved[r.offset] = dd_file_path
                self.output[r.file.path].extracted[r.offset] = ExtractDetails(files=[], command=extraction_utility)

                # Do a directory listing of the output directory
                directory_listing = set(os.listdir(extraction_directory))

                # If this is a newly created output directory, self.last_directory_listing won't have a record of it.
                # If we've extracted other files to this directory before, it
                # will.
                if not has_key(self.last_directory_listing, extraction_directory):
                    self.last_directory_listing[extraction_directory] = set()

                # Loop through a list of newly created files (i.e., files that
                # weren't listed in the last directory listing)
                for f in directory_listing.difference(self.last_directory_listing[extraction_directory]):
                    # Build the full file path and add it to the extractor
                    # results
                    file_path = os.path.join(extraction_directory, f)
                    real_file_path = os.path.realpath(file_path)
                    self.result(description=file_path, display=False)

                    # Also keep a list of files created by the extraction utility.
                    # Report the file_path, not the real_file_path, otherwise symlinks will be resolved and
                    # the same file can end up being listed multiple times if there are symlinks to it.
                    if real_file_path != dd_file_path:
                        binwalk.core.common.debug("Adding %s (%s) (%s) to file list" % (file_path, f, real_file_path))
                        self.output[r.file.path].extracted[r.offset].files.append(file_path)

                    # If recursion was specified, and the file is not the same
                    # one we just dd'd
                    if (self.matryoshka and
                        file_path != dd_file_path and
                        scan_extracted_files and
                            self.directory in real_file_path):
                        # If the recursion level of this file is less than or
                        # equal to our desired recursion level
                        if len(real_file_path.split(self.directory)[1].split(os.path.sep)) <= self.matryoshka:
                            # If this is a directory and we are supposed to process directories for this extractor,
                            # then add all files under that directory to the
                            # list of pending files.
                            if os.path.isdir(file_path):
                                for root, dirs, files in os.walk(file_path):
                                    for f in files:
                                        full_path = os.path.join(root, f)
                                        self.add_pending(full_path)
                            # If it's just a file, it to the list of pending
                            # files
                            else:
                                self.add_pending(file_path)

                # Update the last directory listing for the next time we
                # extract a file to this same output directory
                self.last_directory_listing[
                    extraction_directory] = directory_listing

    def append_rule(self, r):
        self.extract_rules.append(r.copy())

    def prepend_rule(self, r):
        self.extract_rules = [r] + self.extract_rules

    def add_rule(self, txtrule=None, regex=None, extension=None, cmd=None, codes=[0, None], recurse=True, prepend=False):
        rules = self.create_rule(txtrule, regex, extension, cmd, codes, recurse)
        for r in rules:
            if prepend:
                self.prepend_rule(r)
            else:
                self.append_rule(r)

    def create_rule(self, txtrule=None, regex=None, extension=None, cmd=None, codes=[0, None], recurse=True):
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
        created_rules = []
        match = False
        r = {
            'extension': '',
            'cmd': '',
            'regex': None,
            'codes': codes,
            'recurse': recurse,
        }

        # Process single explicitly specified rule
        if not txtrule and regex and extension:
            r['extension'] = extension
            r['regex'] = re.compile(regex)
            if cmd:
                r['cmd'] = cmd

            return [r]

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
                created_rules.append(r)

        return created_rules

    def remove_rules(self, description):
        '''
        Remove all rules that match a specified description.

        @description - The description to match against.

        Returns the number of rules removed.
        '''
        rm = []
        description = description.lower()

        for i in range(0, len(self.extract_rules)):
            if self.extract_rules[i]['regex'].search(description):
                rm.append(i)

        for i in rm:
            self.extract_rules.pop(i)

        return len(rm)

    def edit_rules(self, description, key, value):
        '''
        Edit all rules that match a specified description.

        @description - The description to match against.
        @key         - The key to change for each matching rule.
        @value       - The new key value for each matching rule.

        Returns the number of rules modified.
        '''
        count = 0
        description = description.lower()

        for i in range(0, len(self.extract_rules)):
            if self.extract_rules[i]['regex'].search(description):
                if has_key(self.extract_rules[i], key):
                    self.extract_rules[i][key] = value
                    count += 1

        return count

    def clear_rules(self):
        '''
        Deletes all extraction rules.

        Returns None.
        '''
        self.extract_rules = []

    def get_rules(self, description=None):
        '''
        Returns a list of extraction rules that match a given description.

        @description - The description to match against.

        Returns a list of extraction rules that match the given description.
        If no description is provided, a list of all rules are returned.
        '''
        if description:
            rules = []
            description = description.lower()
            for i in range(0, len(self.extract_rules)):
                if self.extract_rules[i]['regex'].search(description):
                    rules.append(self.extract_rules[i])
        else:
            rules = self.extract_rules

        return rules

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

    def get_output_directory_override(self):
        '''
        Returns the current output directory basename override value.
        '''
        return self.output_directory_override

    def override_output_directory_basename(self, dirname):
        '''
        Allows the overriding of the default extraction directory basename.

        @dirname - The directory base name to use.

        Returns the current output directory basename override value.
        '''
        self.output_directory_override = dirname
        return self.output_directory_override

    def build_output_directory(self, path):
        '''
        Set the output directory for extracted files.

        @path - The path to the file that data will be extracted from.

        Returns None.
        '''
        # If we have not already created an output directory for this target
        # file, create one now
        if not has_key(self.extraction_directories, path):
            basedir = os.path.dirname(path)
            basename = os.path.basename(path)

            if basedir != self.directory:
                # During recursive extraction, extracted files will be in subdirectories
                # of the CWD. This allows us to figure out the subdirectory by simply
                # splitting the target file's base directory on our known CWD.
                #
                # However, the very *first* file being scanned is not necessarily in the
                # CWD, so this will raise an IndexError. This is easy to handle though,
                # since the very first file being scanned needs to have its contents
                # extracted to ${CWD}/_basename.extracted, so we just set the subdir
                # variable to a blank string when an IndexError is encountered.
                try:
                    subdir = basedir.split(self.directory)[1][1:]
                except IndexError as e:
                    subdir = ""
            else:
                subdir = ""

            if self.output_directory_override:
                output_directory = os.path.join(self.directory, subdir, self.output_directory_override)
            else:
                outdir = os.path.join(self.directory, subdir, '_' + basename)
                output_directory = unique_file_name(outdir, extension='extracted')

            if not os.path.exists(output_directory):
                os.mkdir(output_directory)

            self.extraction_directories[path] = output_directory
            self.output[path].directory = os.path.realpath(output_directory) + os.path.sep
        # Else, just use the already created directory
        else:
            output_directory = self.extraction_directories[path]

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
        rule = None
        recurse = False
        command_line = ''
        original_dir = os.getcwd()
        rules = self.match(description)
        file_path = os.path.realpath(file_name)

        # No extraction rules for this file
        if not rules:
            binwalk.core.common.debug("No extraction rules found for '%s'" % description)
            return (None, None, False, str(None))
        else:
            binwalk.core.common.debug("Found %d matching extraction rules" % len(rules))

        # Generate the output directory name where extracted files will be stored
        output_directory = self.build_output_directory(file_name)

        # Extract to end of file if no size was specified
        if not size:
            size = file_size(file_path) - offset

        if os.path.isfile(file_path):
            binwalk.core.common.debug("Changing directory to: %s" % output_directory)
            os.chdir(output_directory)

            # Extract into subdirectories named by the offset
            if self.extract_into_subdirs:
                # Remove trailing L that is added by hex()
                offset_dir = "0x%X" % offset
                os.mkdir(offset_dir)
                os.chdir(offset_dir)

            # Loop through each extraction rule until one succeeds
            for i in range(0, len(rules)):
                rule = rules[i]

                binwalk.core.common.debug("Processing extraction rule #%d (%s)" % (i, str(rule['cmd'])))

                # Make sure we don't recurse into any extracted directories if
                # instructed not to
                if rule['recurse'] in [True, False]:
                    recurse = rule['recurse']
                else:
                    recurse = True

                binwalk.core.common.debug("Extracting %s[%d:] to %s" % (file_path, offset, name))

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

                    binwalk.core.common.debug("Executing extraction command %s" % (str(rule['cmd'])))

                    # Execute the specified command against the extracted file
                    if self.run_extractors:
                        (extract_ok, command_line) = self.execute(rule['cmd'], fname, rule['codes'])
                    else:
                        extract_ok = True
                        command_line = ''

                    binwalk.core.common.debug("Ran extraction command: %s" % command_line)
                    binwalk.core.common.debug("Extraction successful: %s" % extract_ok)

                    # Only clean up files if remove_after_execute was specified.
                    # Only clean up files if the file was extracted sucessfully, or if we've run
                    # out of extractors.
                    if self.remove_after_execute and (extract_ok == True or i == (len(rules) - 1)):

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
                    # If it is the last rule, leave the file on disk for the
                    # user to examine.
                    elif i != (len(rules) - 1):
                        try:
                            os.unlink(fname)
                        except KeyboardInterrupt as e:
                            raise e
                        except Exception as e:
                            pass

                # If there was no command to execute, just use the first rule
                else:
                    break

            binwalk.core.common.debug("Changing directory back to: %s" % original_dir)
            os.chdir(original_dir)

        return (output_directory, fname, recurse, command_line)

        #if rule is not None:
        #    if callable(rule['cmd']):
        #        command_name = get_class_name_from_method(rule['cmd'])
        #    else:
        #        command_name = rule['cmd']
        #    return (output_directory, fname, recurse, command_name)
        #else:
        #    return (output_directory, fname, recurse, '')

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
        ordered_rules = []
        description = description.lower()

        for rule in self.extract_rules:
            if rule['regex'].search(description):
                rules.append(rule)

        # Plugin rules should take precedence over external extraction commands.
        for rule in rules:
            if callable(rule['cmd']):
                ordered_rules.append(rule)
        for rule in rules:
            if not callable(rule['cmd']):
                ordered_rules.append(rule)

        return ordered_rules

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

        # Make sure the output file name is a string
        if output_file_name is not None:
            output_file_name = str(output_file_name)

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
                if dlen < 1:
                    break
                else:
                    total_size += (dlen - adjust)
                    if total_size > size:
                        dlen -= (total_size - size)
                    fdout.write(str2bytes(data[adjust:dlen]))
                    adjust = 0

            # Cleanup
            fdout.close()
            fdin.close()
        except KeyboardInterrupt as e:
            raise e
        except Exception as e:
            raise Exception("Extractor.dd failed to extract data from '%s' to '%s': %s" %
                            (file_name, fname, str(e)))

        binwalk.core.common.debug("Carved data block 0x%X - 0x%X from '%s' to '%s'" %
                                  (offset, offset + size, file_name, fname))
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
        command_list = []

        binwalk.core.common.debug("Running extractor '%s'" % str(cmd))

        try:
            if callable(cmd):
                command_list.append(get_class_name_from_method(cmd))

                try:
                    retval = cmd(fname)
                except KeyboardInterrupt as e:
                    raise e
                except Exception as e:
                    retval = False
                    binwalk.core.common.warning("Internal extractor '%s' failed with exception: '%s'" % (str(cmd), str(e)))
            elif cmd:
                # If not in debug mode, create a temporary file to redirect
                # stdout and stderr to
                if not binwalk.core.common.DEBUG:
                    tmp = tempfile.TemporaryFile()

                # Generate unique file paths for all paths in the current
                # command that are surrounded by UNIQUE_PATH_DELIMITER
                while self.UNIQUE_PATH_DELIMITER in cmd:
                    need_unique_path = cmd.split(self.UNIQUE_PATH_DELIMITER)[
                        1].split(self.UNIQUE_PATH_DELIMITER)[0]
                    unique_path = binwalk.core.common.unique_file_name(need_unique_path)
                    cmd = cmd.replace(self.UNIQUE_PATH_DELIMITER + need_unique_path + self.UNIQUE_PATH_DELIMITER, unique_path)

                # Execute.
                for command in cmd.split("&&"):

                    # Replace all instances of FILE_NAME_PLACEHOLDER in the
                    # command with fname
                    command = command.strip().replace(self.FILE_NAME_PLACEHOLDER, fname)

                    binwalk.core.common.debug("subprocess.call(%s, stdout=%s, stderr=%s)" % (command, str(tmp), str(tmp)))
                    rval = subprocess.call(shlex.split(command), stdout=tmp, stderr=tmp)

                    if rval in codes:
                        retval = True
                    else:
                        retval = False

                    binwalk.core.common.debug('External extractor command "%s" completed with return code %d (success: %s)' % (cmd, rval, str(retval)))
                    command_list.append(command)

                    # TODO: Should errors from all commands in a command string be checked? Currently we only support
                    #       specifying one set of error codes, so at the moment, this is not done; it is up to the
                    #       final command to return success or failure (which presumably it will if previous necessary
                    #       commands were not successful, but this is an assumption).
                    # if retval == False:
                    #    break

        except KeyboardInterrupt as e:
            raise e
        except Exception as e:
            binwalk.core.common.warning("Extractor.execute failed to run external extractor '%s': %s, '%s' might not be installed correctly" % (str(cmd), str(e), str(cmd)))
            retval = None

        if tmp is not None:
            tmp.close()

        return (retval, '&&'.join(command_list))
