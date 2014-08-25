# Performs extraction of data that matches extraction rules.
# This is automatically invoked by core.module code if extraction has been
# enabled by the user; other modules need not reference this module directly.

import os
import re
import sys
import shlex
import tempfile
import subprocess
import binwalk.core.common
from binwalk.core.compat import *
from binwalk.core.module import Module, Option, Kwarg
from binwalk.core.common import file_size, unique_file_name, BlockFile

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
            Option(short='j',
                   long='size',
                   type=int,
                   kwargs={'max_size' : 0},
                   description='Limit the size of each extracted file'),
            Option(short='r',
                   long='rm',
                   kwargs={'remove_after_execute' : True},
                   description='Cleanup extracted / zero-size files after extraction'),
            Option(short='z',
                   long='carve',
                   kwargs={'run_extractors' : False},
                   description="Carve data from files, but don't execute extraction utilities"),
    ]

    KWARGS = [
            Kwarg(name='max_size', default=None),
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

        if self.load_default_rules:
            self.load_defaults()

        for manual_rule in self.manual_rules:
            self.add_rule(manual_rule)

        if self.matryoshka:
            self.config.verbose = True

    def reset(self):
        # Holds a list of pending files that should be scanned; only populated if self.matryoshka == True
        self.pending = []
        # Holds a dictionary of extraction directories created for each scanned file.
        self.extraction_directories = {}
        # Holds a dictionary of the last directory listing for a given directory; used for identifying
        # newly created/extracted files that need to be appended to self.pending.
        self.last_directory_listing = {}
        # Set to the directory path of the first extracted directory; this allows us to track recursion depth.
        self.base_recursion_dir = ""

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

        if r.valid:
            binwalk.core.common.debug("Extractor callback for %s:%d [%s & %s & %s]" % (r.file.name, r.offset, str(r.valid), str(r.display), str(r.extract)))
       
        # Only extract valid results that have been marked for extraction and displayed to the user.
        # Note that r.display is still True even if --quiet has been specified; it is False if the result has been
        # explicitly excluded via the -y/-x options.
        if r.valid and r.extract and r.display:
            # Do the extraction
            binwalk.core.common.debug("Attempting extraction...")
            (extraction_directory, dd_file) = self.extract(r.offset, r.description, r.file.name, size, r.name)

            # If the extraction was successful, self.extract will have returned the output directory and name of the dd'd file
            if extraction_directory and dd_file:
                # Get the full path to the dd'd file
                dd_file_path = os.path.join(extraction_directory, dd_file)

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

                    # If recursion was specified, and the file is not the same one we just dd'd, and if it is not a directory
                    if self.matryoshka and file_path != dd_file_path and not os.path.isdir(file_path):
                        # If the recursion level of this file is less than or equal to our desired recursion level
                        if len(real_file_path.split(self.base_recursion_dir)[1].split(os.path.sep)) <= self.matryoshka:
                            # Add the file to our list of pending files
                            self.pending.append(file_path)

                # Update the last directory listing for the next time we extract a file to this same output directory
                self.last_directory_listing[extraction_directory] = directory_listing

    def append_rule(self, r):
        self.extract_rules.append(r.copy())

    def add_rule(self, txtrule=None, regex=None, extension=None, cmd=None):
        '''
        Adds a set of rules to the extraction rule list.

        @txtrule   - Rule string, or list of rule strings, in the format <regular expression>:<file extension>[:<command to run>]
        @regex     - If rule string is not specified, this is the regular expression string to use.
        @extension - If rule string is not specified, this is the file extension to use.
        @cmd       - If rule string is not specified, this is the command to run.
                     Alternatively a callable object may be specified, which will be passed one argument: the path to the file to extract.

        Returns None.
        '''
        rules = []
        match = False
        r = {
            'extension'    : '',
            'cmd'        : '',
            'regex'        : None
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
            output_directory = os.path.join(os.path.dirname(path), unique_file_name('_' + os.path.basename(path), extension='extracted'))

            if not os.path.exists(output_directory):
                os.mkdir(output_directory)

            self.extraction_directories[path] = output_directory
        # Else, just use the already created directory
        else:
            output_directory = self.extraction_directories[path]

        # Set the initial base extraction directory for later determining the level of recusion
        if not self.base_recursion_dir:
            self.base_recursion_dir = os.path.realpath(output_directory) + os.path.sep

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
        cleanup_extracted_fname = True
        original_dir = os.getcwd()
        rules = self._match(description)
        file_path = os.path.realpath(file_name)

        # No extraction rules for this file
        if not rules:
            return (None, None)

        output_directory = self.build_output_directory(file_name)

        # Extract to end of file if no size was specified    
        if not size:
            size = file_size(file_path) - offset
                
        if os.path.isfile(file_path):
            os.chdir(output_directory)
            
            # Loop through each extraction rule until one succeeds
            for i in range(0, len(rules)):
                rule = rules[i]

                # Copy out the data to disk, if we haven't already
                fname = self._dd(file_path, offset, size, rule['extension'], output_file_name=name)

                # If there was a command specified for this rule, try to execute it.
                # If execution fails, the next rule will be attempted.
                if rule['cmd']:

                    # Many extraction utilities will extract the file to a new file, just without
                    # the file extension (i.e., myfile.7z -> myfile). If the presumed resulting
                    # file name already exists before executing the extract command, do not attempt 
                    # to clean it up even if its resulting file size is 0.
                    if self.remove_after_execute:
                        extracted_fname = os.path.splitext(fname)[0]
                        if os.path.exists(extracted_fname):
                            cleanup_extracted_fname = False

                    # Execute the specified command against the extracted file
                    if self.run_extractors:
                        extract_ok = self.execute(rule['cmd'], fname)
                    else:
                        extract_ok = True

                    # Only clean up files if remove_after_execute was specified                
                    if extract_ok == True and self.remove_after_execute:

                        # Remove the original file that we extracted
                        try:
                            os.unlink(fname)
                        except KeyboardInterrupt as e:
                            raise e
                        except Exception as e:
                            pass

                        # If the command worked, assume it removed the file extension from the extracted file
                        # If the extracted file name file exists and is empty, remove it
                        if cleanup_extracted_fname and os.path.exists(extracted_fname) and file_size(extracted_fname) == 0:
                            try:
                                os.unlink(extracted_fname)
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

        return (output_directory, fname)

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

    def _match(self, description):
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

        Returns an array of ['<case insensitive matching string>', '<file extension>', '<command to run>'].
        '''
        return rule.strip().split(self.RULE_DELIM, 2)

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
        # Default extracted file name is <hex offset>.<extension>
        default_bname = "%X" % offset

        if self.max_size and size > self.max_size:
            size = self.max_size

        if not output_file_name or output_file_name is None:
            bname = default_bname
        else:
            # Strip the output file name of invalid/dangerous characters (like file paths)    
            bname = os.path.basename(output_file_name)
        
        fname = unique_file_name(bname, extension)
            
        try:
            # Open the target file and seek to the offset
            fdin = self.config.open_file(file_name, length=size, offset=offset)
            
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
                    fdout.write(str2bytes(data[:dlen]))
                    total_size += dlen

            # Cleanup
            fdout.close()
            fdin.close()
        except KeyboardInterrupt as e:
            raise e
        except Exception as e:
            raise Exception("Extractor.dd failed to extract data from '%s' to '%s': %s" % (file_name, fname, str(e)))
       
        binwalk.core.common.debug("Carved data block 0x%X - 0x%X from '%s' to '%s'" % (offset, offset+size, file_name, fname)) 
        return fname

    def execute(self, cmd, fname):
        '''
        Execute a command against the specified file.

        @cmd   - Command to execute.
        @fname - File to run command against.

        Returns True on success, False on failure, or None if the external extraction utility could not be found.
        '''
        tmp = None
        rval = 0
        retval = True

        binwalk.core.common.debug("Running extractor '%s'" % str(cmd))

        try:
            if callable(cmd):
                try:
                    cmd(fname)
                except KeyboardInterrupt as e:
                    raise e
                except Exception as e:
                    binwalk.core.common.warning("Extractor.execute failed to run internal extractor '%s': %s" % (str(cmd), str(e)))
            else:
                # If not in debug mode, create a temporary file to redirect stdout and stderr to
                if not binwalk.core.common.DEBUG:
                    tmp = tempfile.TemporaryFile()

                # Execute.
                for command in cmd.split("&&"):
                    # Replace all instances of FILE_NAME_PLACEHOLDER in the command with fname
                    command = command.strip().replace(self.FILE_NAME_PLACEHOLDER, fname)

                    binwalk.core.common.debug("subprocess.call(%s, stdout=%s, stderr=%s)" % (command, str(tmp), str(tmp)))    
                    rval = subprocess.call(shlex.split(command), stdout=tmp, stderr=tmp)
                    binwalk.core.common.debug('External extractor command "%s" completed with return code %d' % (cmd, rval))
                    
                    if rval == 0:
                        retval = True
                    else:
                        retval = False
                        break

        except KeyboardInterrupt as e:
            raise e
        except Exception as e:
            # Silently ignore no such file or directory errors. Why? Because these will inevitably be raised when
            # making the switch to the new firmware mod kit directory structure. We handle this elsewhere, but it's
            # annoying to see this spammed out to the console every time.
            if binwalk.core.common.DEBUG or (not hasattr(e, 'errno') or e.errno != 2):
                binwalk.core.common.warning("Extractor.execute failed to run external extrator '%s': %s" % (str(cmd), str(e)))
            retval = None
        
        if tmp is not None:
            tmp.close()

        return retval
    

