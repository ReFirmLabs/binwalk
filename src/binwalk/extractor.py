import os
import re
import sys
import shlex
import tempfile
import subprocess
from binwalk.compat import *
from binwalk.config import *
from binwalk.common import file_size, unique_file_name, BlockFile

class Extractor:
	'''
	Extractor class, responsible for extracting files from the target file and executing external applications, if requested.
	An instance of this class is accessible via the Binwalk.extractor object.

	Example usage:

		import binwalk
		
		bw = binwalk.Binwalk()

		# Create extraction rules for scan results containing the string 'gzip compressed data' and 'filesystem'.
		# The former will be saved to disk with a file extension of 'gz' and the command 'gunzip <file name on disk>' will be executed (note the %e placeholder).
		# The latter will be saved to disk with a file extension of 'fs' and no command will be executed.
		# These rules will be ignored if there were previous rules with the same match string.
		bw.extractor.add_rule(['gzip compressed data:gz:gunzip %e', 'filesystem:fs'])

		# Load the extraction rules from the default extract.conf file(s).
		bw.extractor.load_defaults()

		# Run the binwalk scan.
		bw.scan('firmware.bin')
		
	'''
	# Extract rules are delimited with a colon.
	# <case insensitive matching string>:<file extension>[:<command to run>]
	RULE_DELIM = ':'

	# Comments in the extract.conf files start with a pound
	COMMENT_DELIM ='#'

	# Place holder for the extracted file name in the command 
	FILE_NAME_PLACEHOLDER = '%e'

	# Max size of data to read/write at one time when extracting data
	MAX_READ_SIZE = 10 * 1024 * 1024

	def __init__(self, verbose=False, exec_commands=True, max_size=None):
		'''
		Class constructor.
	
		@verbose       - Set to True to display the output from any executed external applications.
		@exec_commands - Set to False to disable the execution of external utilities when extracting data from files.
		@max_size      - Limit the size of extracted files to max_size.

		Returns None.
		'''
		self.config = Config()
		self.enabled = False
		self.delayed = True
		self.verbose = verbose
		self.max_size = max_size
		self.exec_commands = exec_commands
		self.extract_rules = []
		self.remove_after_execute = False
		self.extract_path = os.getcwd()

	def append_rule(self, r):
		self.enabled = True
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
			'extension'	: '',
			'cmd'		: '',
			'regex'		: None
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
			except:
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
		self.enabled = False

	def get_rules(self):
		'''
		Returns a list of all extraction rules.
		'''
		return self.extract_rules

	def enable_delayed_extract(self, tf=None):
		'''
		Enables / disables the delayed extraction feature.
		This feature ensures that certian supported file types will not contain extra data at the end of the
		file when they are extracted, but also means that these files will not be extracted until the end of the scan.

		@tf - Set to True to enable, False to disable. 

		Returns the current delayed extraction setting.
		'''
		if tf is not None:
			self.delayed = tf
		return self.delayed

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
		except Exception as e:
			raise Exception("Extractor.load_from_file failed to load file '%s': %s" % (fname, str(e)))

	def load_defaults(self):
		'''
		Loads default extraction rules from the user and system extract.conf files.

		Returns None.
		'''
		# Load the user extract file first to ensure its rules take precedence.
		extract_files = [
			self.config.paths['user'][self.config.EXTRACT_FILE],
			self.config.paths['system'][self.config.EXTRACT_FILE],
		]

		for extract_file in extract_files:
			try:
				self.load_from_file(extract_file)
			except Exception as e:
				if self.verbose:
					raise Exception("Extractor.load_defaults failed to load file '%s': %s" % (extract_file, str(e)))

	def output_directory(self, path):
		'''
		Set the output directory for extracted files.

		@path - The extraction path.

		Returns None.
		'''
		self.extract_path = path

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

		# No extraction rules for this file
		if not rules:
			return

		if not os.path.exists(self.extract_path):
			os.mkdir(self.extract_path)

		file_path = os.path.realpath(file_name)
		
		if os.path.isfile(file_path):
			os.chdir(self.extract_path)
			
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
					extract_ok = self.execute(rule['cmd'], fname)

					# Only clean up files if remove_after_execute was specified				
					if extract_ok and self.remove_after_execute:

						# Remove the original file that we extracted
						try:
							os.unlink(fname)
						except:
							pass

						# If the command worked, assume it removed the file extension from the extracted file
						# If the extracted file name file exists and is empty, remove it
						if cleanup_extracted_fname and os.path.exists(extracted_fname) and file_size(extracted_fname) == 0:
							try:
								os.unlink(extracted_fname)
							except:
								pass
					
					# If the command executed OK, don't try any more rules
					if extract_ok:
						break
					# Else, remove the extracted file if this isn't the last rule in the list.
					# If it is the last rule, leave the file on disk for the user to examine.
					elif i != (len(rules)-1):
						try:
							os.unlink(fname)
						except:
							pass

				# If there was no command to execute, just use the first rule
				else:
					break

			os.chdir(original_dir)

		# If a file was extracted, return the full path to that file	
		if fname:
			fname = os.path.join(self.extract_path, fname)

		return fname

	def delayed_extract(self, results, file_name, size):
		'''
		Performs a delayed extraction (see self.enable_delayed_extract).
		Called internally by Binwalk.Scan().

		@results   - A list of dictionaries of all the scan results.
		@file_name - The path to the scanned file.
		@size      - The size of the scanned file.

		Returns an updated results list containing the names of the newly extracted files.
		'''
		index = 0
		info_count = 0
		nresults = results

		for (offset, infos) in results:
			info_count = 0

			for info in infos:
				ninfos = infos

				if info['delay']:
					end_offset = self._entry_offset(index, results, info['delay'])
					if end_offset == -1:
						extract_size = size
					else:
						extract_size = (end_offset - offset)

					ninfos[info_count]['extract'] = self.extract(offset, info['description'], file_name, extract_size, info['name'])
					nresults[index] = (offset, ninfos)

				info_count += 1

			index += 1
		
		return nresults

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
			fdin = BlockFile(file_name, 'r', length=size)
			fdin.seek(offset)
			
			# Open the output file
			try:
				fdout = BlockFile(fname, 'w')
			except Exception as e:
				# Fall back to the default name if the requested name fails
				fname = unique_file_name(default_bname, extension)
				fdout = BlockFile(fname, 'w')

			while total_size < size:
				(data, dlen) = fdin.read_block()
				fdout.write(str2bytes(data[:dlen]))
				total_size += dlen

			# Cleanup
			fdout.close()
			fdin.close()
		except Exception as e:
			raise Exception("Extractor.dd failed to extract data from '%s' to '%s': %s" % (file_name, fname, str(e)))
		
		return fname

	def execute(self, cmd, fname):
		'''
		Execute a command against the specified file.

		@cmd   - Command to execute.
		@fname - File to run command against.

		Returns True on success, False on failure.
		'''
		tmp = None
		retval = True

		if not self.exec_commands:
			return retval

		try:
			if callable(cmd):
				try:
					cmd(fname)
				except Exception as e:
					sys.stderr.write("WARNING: Extractor.execute failed to run '%s': %s\n" % (str(cmd), str(e)))
			else:
				# If not in verbose mode, create a temporary file to redirect stdout and stderr to
				if not self.verbose:
					tmp = tempfile.TemporaryFile()

				# Replace all instances of FILE_NAME_PLACEHOLDER in the command with fname
				cmd = cmd.replace(self.FILE_NAME_PLACEHOLDER, fname)
	
				# Execute.
				if subprocess.call(shlex.split(cmd), stdout=tmp, stderr=tmp) != 0:
					retval = False
		except Exception as e:
			# Silently ignore no such file or directory errors. Why? Because these will inevitably be raised when
			# making the switch to the new firmware mod kit directory structure. We handle this elsewhere, but it's
			# annoying to see this spammed out to the console every time.
			if e.errno != 2:
				sys.stderr.write("WARNING: Extractor.execute failed to run '%s': %s\n" % (str(cmd), str(e)))
			retval = False
		
		if tmp is not None:
			tmp.close()

		return retval
	

