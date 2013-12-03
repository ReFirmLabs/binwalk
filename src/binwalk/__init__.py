__all__ = ["Binwalk"]

import os
import re
import time
import magic
from binwalk.compat import *
from binwalk.config import *
from binwalk.update import *
from binwalk.filter import *
from binwalk.parser import *
from binwalk.plugins import *
from binwalk.plotter import *
from binwalk.hexdiff import *
from binwalk.entropy import *
from binwalk.extractor import *
from binwalk.prettyprint import *
from binwalk.smartstrings import *
from binwalk.smartsignature import *
from binwalk.common import file_size, unique_file_name, BlockFile

class Binwalk(object):
	'''
	Primary Binwalk class.

	Useful class objects:

		self.filter        - An instance of the MagicFilter class.
		self.extractor     - An instance of the Extractor class.
		self.parser        - An instance of the MagicParser class.
		self.display       - An instance of the PrettyPrint class.
		self.magic_files   - A list of magic file path strings to use whenever the scan() method is invoked.
		self.scan_length   - The total number of bytes to be scanned.
		self.total_scanned - The number of bytes that have already been scanned.
		self.scan_type     - The type of scan being performed, one of: BINWALK, BINCAST, BINARCH, STRINGS, ENTROPY.

	Performing a simple binwalk scan:

		from binwalk import Binwalk
			
		scan = Binwalk().scan(['firmware1.bin', 'firmware2.bin'])
		for (filename, file_results) in scan.iteritems():
			print "Results for %s:" % filename
			for (offset, results) in file_results:
				for result in results:
					print offset, result['description']
	'''

	# Default libmagic flags. Basically disable anything we don't need in the name of speed.
	DEFAULT_FLAGS = magic.MAGIC_NO_CHECK_TEXT | magic.MAGIC_NO_CHECK_ENCODING | magic.MAGIC_NO_CHECK_APPTYPE | magic.MAGIC_NO_CHECK_TOKENS

	# Maximum magic bytes length
	MAX_SIGNATURE_SIZE = 128

	# Minimum verbosity level at which to enable extractor verbosity.
	VERY_VERBOSE = 2

	# Scan every byte by default.
	DEFAULT_BYTE_ALIGNMENT = 1

	# Valid scan_type values.
	# ENTROPY must be the largest value to ensure it is performed last if multiple scans are performed.
	BINWALK = 0x01
	BINARCH = 0x02
	BINCAST = 0x03
	STRINGS = 0x04
	COMPRESSION = 0x05
	HEXDIFF = 0x06
	CUSTOM = 0x07
	BINVIS = 0x08
	ENTROPY = 0x09

	def __init__(self, magic_files=[], flags=magic.MAGIC_NONE, log=None, quiet=False, verbose=0, ignore_smart_keywords=False, ignore_time_skews=False, load_extractor=False, load_plugins=True, exec_commands=True, max_extract_size=None):
		'''
		Class constructor.

		@magic_files            - A list of magic files to use.
		@flags                  - Flags to pass to magic_open. [TODO: Might this be more appropriate as an argument to load_signaures?]
		@log                    - Output PrettyPrint data to log file as well as to stdout.
		@quiet                  - If set to True, supress PrettyPrint output to stdout.
		@verbose                - Verbosity level.
		@ignore_smart_keywords  - Set to True to ignore smart signature keywords.
		@ignore_time_skews      - Set to True to ignore file results with timestamps in the future.
		@load_extractor         - Set to True to load the default extraction rules automatically.
		@load_plugins           - Set to False to disable plugin support.
		@exec_commands          - Set to False to disable the execution of external utilities when extracting data from files.
		@max_extract_size       - Limit the size of extracted files.

		Returns None.
		'''
		self.flags = self.DEFAULT_FLAGS | flags
		self.last_extra_data_section = ''
		self.load_plugins = load_plugins
		self.magic_files = magic_files
		self.verbose = verbose
		self.total_scanned = 0
		self.scan_length = 0
		self.total_read = 0
		self.matryoshka = 1
		self.epoch = 0
		self.year = 0
		self.plugins = None
		self.magic = None
		self.mfile = None
		self.entropy = None
		self.strings = None
		self.scan_type = self.BINWALK

		if not ignore_time_skews:
			# Consider timestamps up to 1 year in the future valid,
			# to account for any minor time skew on the local system.
			self.year = time.localtime().tm_year + 1
			self.epoch = int(time.time()) + (60 * 60 * 24 * 365)

		# Instantiate the config class so we can access file/directory paths
		self.config = Config()

		# Use the system default magic file if no other was specified
		if not self.magic_files or self.magic_files is None:
			# Append the user's magic file first so that those signatures take precedence
			self.magic_files = [
					self.config.paths['user'][self.config.BINWALK_MAGIC_FILE],
					self.config.paths['system'][self.config.BINWALK_MAGIC_FILE],
			]

		# Only set the extractor verbosity if told to be very verbose
		if self.verbose >= self.VERY_VERBOSE:
			extractor_verbose = True
		else:
			extractor_verbose = False

		# Create an instance of the PrettyPrint class, which can be used to print results to screen/file.
		self.display = PrettyPrint(self, log=log, quiet=quiet, verbose=verbose)

		# Create MagicFilter and Extractor class instances. These can be used to:
		#
		#	o Create include/exclude filters
		#	o Specify file extraction rules to be applied during a scan
		#
		self.filter = MagicFilter()
		self.extractor = Extractor(verbose=extractor_verbose, exec_commands=exec_commands, max_size=max_extract_size)
		if load_extractor:
			self.extractor.load_defaults()

		# Create SmartSignature and MagicParser class instances. These are mostly for internal use.
		self.smart = SmartSignature(self.filter, ignore_smart_signatures=ignore_smart_keywords)
		self.parser = MagicParser(self.filter, self.smart)

	def __del__(self):
		self.cleanup()

	def __enter__(self):
		return self

	def __exit__(self, t, v, traceback):
		self.cleanup()

	def cleanup(self):
		'''
		Close magic and cleanup any temporary files generated by the internal instance of MagicParser.

		Returns None.
		'''
		try:
			self.magic.close()
		except:
			pass

		try:
			self.parser.cleanup()
		except:
			pass

	def load_signatures(self, magic_files=[]):
		'''
		Load signatures from magic file(s).
		Called automatically by Binwalk.scan() with all defaults, if not already called manually.

		@magic_files - A list of magic files to use (default: self.magic_files).
	
		Returns None.	
		'''
		# The magic files specified here override any already set
		if magic_files and magic_files is not None:
			self.magic_files = magic_files

		# Parse the magic file(s) and initialize libmagic
		self.mfile = self.parser.parse(self.magic_files)
		self.magic = magic.open(self.flags)
		self.magic.load(str2bytes(self.mfile))
		# Once the temporary magic file is loaded into libmagic, we don't need it anymore; delete the temp file
		self.parser.rm_magic_file()

	def hexdiff(self, file_names, length=0x100, offset=0, block=16, first=False):
		if not length and len(file_names) > 0:
			length = file_size(file_names[0])
		if not block:
			block = 16

		HexDiff(self).display(file_names, offset=offset, size=length, block=block, show_first_only=first)

	def analyze_strings(self, file_names, length=0, offset=0, n=0, block=0, load_plugins=True, whitelist=[], blacklist=[]):
		'''
		Performs a strings analysis on the specified file(s).

		@file_names   - A list of files to analyze.
		@length       - The number of bytes in the file to analyze.
		@offset       - The starting offset into the file to begin analysis.
		@n            - The minimum valid string length.
		@block        - The block size to use when performing entropy analysis.
		@load_plugins - Set to False to disable plugin callbacks.
		@whitelist    - A list of whitelisted plugins.
		@blacklist    - A list of blacklisted plugins.
		
		Returns a dictionary compatible with other classes and methods (Entropy, Binwalk, analyze_entropy, etc):

			{
				'file_name' : (offset, [{
								'description' : 'Strings',
								'string'      : 'found_string'
							}]
					)
			}
		'''
		data = {}

		self.strings = Strings(file_names,
					self,
					length=length, 
					offset=offset,
					n=n,
					block=block,
					algorithm='gzip',		# Use gzip here as it is faster and we don't need the detail provided by shannon
					load_plugins=load_plugins,
					whitelist=whitelist,
					blacklist=blacklist)

		data = self.strings.strings()
		
		del self.strings
		self.strings = None

		return data

	def analyze_entropy(self, files, offset=0, length=0, block=0, plot=True, legend=True, save=False, algorithm=None, load_plugins=True, whitelist=[], blacklist=[], compcheck=False):
		'''
		Performs an entropy analysis on the specified file(s).

		@files        - A dictionary containing file names and results data, as returned by Binwalk.scan.
		@offset       - The offset into the data to begin analysis.
		@length       - The number of bytes to analyze.
		@block        - The size of the data blocks to analyze.
		@plot         - Set to False to disable plotting.
		@legend       - Set to False to exclude the legend and custom offset markers from the plot.
		@save         - Set to True to save plots to disk instead of displaying them.
		@algorithm    - Set to 'gzip' to use the gzip entropy "algorithm".
		@load_plugins - Set to False to disable plugin callbacks.
		@whitelist    - A list of whitelisted plugins.
		@blacklist    - A list of blacklisted plugins.
		@compcheck    - Set to True to perform heuristic compression detection.

		Returns a dictionary of:
                        
			{
				'file_name' : ([list, of, offsets], [list, of, entropy], average_entropy)
			}
		'''
		data = {}

		self.entropy = Entropy(files,
					self,
					offset,
					length,
					block,
					plot,
					legend,
					save,
					algorithm=algorithm,
					load_plugins=plugins,
					whitelist=whitelist,
					blacklist=blacklist,
					compcheck=compcheck)
		
		data = self.entropy.analyze()
		
		del self.entropy
		self.entropy = None

		return data

	def plot3d(self, target_files, offset=0, length=0, weight=None, show_grids=False, verbose=False):
		'''
		Generates a 3D data plot of the specified target files.

		@target_files   - File or list of files to scan.
		@offset         - Starting offset at which to start the scan.
                @length         - Number of bytes to scan. Specify 0 to scan the entire file(s).
		@weight         - A data point must occur at least this many times before being plotted (default: auto-detect).
		@show_grids     - Set to True to show axis grids in the 3D plot.
		@verbose        - Set to True to enable verbose output.

		Returns None.
		'''
		if not isinstance(target_files, type([])):
			target_files = [target_files]

		Plotter3D(target_files, offset=offset, length=length, weight=weight, show_grids=show_grids, verbose=verbose).plot()

	def scan(self, target_files, offset=0, length=0, show_invalid_results=False, callback=None, start_callback=None, end_callback=None, base_dir=None, matryoshka=1, plugins_whitelist=[], plugins_blacklist=[]):
		'''
		Performs a binwalk scan on a file or list of files.

		@target_files         - File or list of files to scan.
		@offset               - Starting offset at which to start the scan.
                @length               - Number of bytes to scan. Specify -1 for streams.
                @show_invalid_results - Set to True to display invalid results.
                @callback             - Callback function to be invoked when matches are found.
		@start_callback       - Callback function to be invoked prior to scanning each file.
		@end_callback         - Callback function to be invoked after scanning each file.
		@base_dir             - Base directory for output files.
		@matryoshka           - Number of levels to traverse into the rabbit hole.
		@plugins_whitelist    - A list of plugin names to load. If not empty, only these plugins will be loaded.
		@plugins_blacklist    - A list of plugin names to not load.

		Returns a dictionary of :

			{
				'target file name' : [
							(0, [{description : "LZMA compressed data..."}]),
							(112, [{description : "gzip compressed data..."}])
				]
			}
		'''
		# Prefix all directory names with an underscore. This prevents accidental deletion of the original file(s)
		# when the user is typing too fast and is trying to deleted the extraction directory.
		prefix = '_'
		dir_extension = 'extracted'
		i = 0
		total_results = {}
		self.matryoshka = matryoshka

		# For backwards compatibility
		if not isinstance(target_files, type([])):
			target_files = [target_files]

		if base_dir is None:
			base_dir = ''

		# Instantiate the Plugins class and load all plugins, if not disabled
		self.plugins = Plugins(self, whitelist=plugins_whitelist, blacklist=plugins_blacklist)
		if self.load_plugins:
			self.plugins._load_plugins()

		# Load the default signatures if self.load_signatures has not already been invoked
		if self.magic is None:
			self.load_signatures()

		while i < self.matryoshka:
			new_target_files = []

			# Scan each target file
			for target_file in target_files:
				ignore_files = []

				# On the first scan, add the base_dir value to dir_prefix. Subsequent target_file values will have this value prepended already.
				if i == 0:
					dir_prefix = os.path.join(base_dir, prefix + os.path.basename(target_file))
				else:
					dir_prefix = os.path.join(os.path.dirname(target_file), prefix + os.path.basename(target_file))

				output_dir = unique_file_name(dir_prefix, dir_extension)

				# Set the output directory for extracted files to go to
				self.extractor.output_directory(output_dir)

				if start_callback is not None:
					start_callback(target_file)
	
				results = self.single_scan(target_file, 
							offset=offset, 
							length=length, 
							show_invalid_results=show_invalid_results,
							callback=callback)
	
				if end_callback is not None:
					end_callback(target_file)

				# Get a list of extracted file names; don't scan them again.
				for (index, results_list) in results:
					for result in results_list:
						if result['extract']:
							ignore_files.append(result['extract'])

				# Find all newly created files and add them to new_target_files / new_target_directories
				for (dir_path, sub_dirs, files) in os.walk(output_dir):
					for fname in files:
						fname = os.path.join(dir_path, fname)
						if fname not in ignore_files:
							new_target_files.append(fname)

					# Don't worry about sub-directories
					break

				total_results[target_file] = results

			target_files = new_target_files
			i += 1

		# Be sure to delete the Plugins instance so that there isn't a lingering reference to
		# this Binwalk class instance (lingering handles to this Binwalk instance cause the
		# __del__ deconstructor to not be called).
		if self.plugins is not None:
			del self.plugins
			self.plugins = None

		return total_results

	def single_scan(self, target_file='', fd=None, offset=0, length=0, show_invalid_results=False, callback=None, plugins_whitelist=[], plugins_blacklist=[]):
		'''
		Performs a binwalk scan on one target file or file descriptor.

		@target_file 	      - File to scan.
		@fd                   - A common.BlockFile object.
		@offset      	      - Starting offset at which to start the scan.
		@length      	      - Number of bytes to scan. Specify -1 for streams.
		@show_invalid_results - Set to True to display invalid results.
		@callback    	      - Callback function to be invoked when matches are found.
		@plugins_whitelist    - A list of plugin names to load. If not empty, only these plugins will be loaded.
		@plugins_blacklist    - A list of plugin names to not load.

		The callback function is passed two arguments: a list of result dictionaries containing the scan results
		(one result per dict), and the offset at which those results were identified. Example callback function:

			def my_callback(offset, results):
				print "Found %d results at offset %d:" % (len(results), offset)
				for result in results:
					print "\t%s" % result['description']

			binwalk.Binwalk(callback=my_callback).scan("firmware.bin")

		Upon completion, the scan method returns a sorted list of tuples containing a list of results dictionaries
		and the offsets at which those results were identified:

			scan_results = [
					(0, [{description : "LZMA compressed data..."}]),
					(112, [{description : "gzip compressed data..."}])
			]

		See SmartSignature.parse for a more detailed description of the results dictionary structure.
		'''
		scan_results = {}
		fsize = 0
		jump_offset = 0
		i_opened_fd = False
		i_loaded_plugins = False
		plugret = PLUGIN_CONTINUE
		plugret_start = PLUGIN_CONTINUE
		self.total_read = 0
		self.total_scanned = 0
		self.scan_length = length
		self.filter.show_invalid_results = show_invalid_results
		self.start_offset = offset

		# Check to make sure either a target file or a file descriptor was supplied
		if not target_file and fd is None:
			raise Exception("Must supply Binwalk.single_scan with a valid file path or BlockFile object")

		# Need the total size of the target file, even if we aren't scanning the whole thing
		if target_file:
			fsize = file_size(target_file)
			
		# If no length was specified, make the length the size of the target file minus the starting offset
		if self.scan_length == 0:
			self.scan_length = fsize - offset

		# Open the target file and seek to the specified start offset
		if fd is None:
			fd = BlockFile(target_file, length=self.scan_length, offset=offset)
			i_opened_fd = True
			# If offset is negative (bytes from EOF), BlockFile class will autmoatically calculate the right offset
			offset = fd.offset

		# Seek to the starting offset.
		#fd.seek(offset)
		
		# If the Plugins class has not already been instantitated, do that now.
		if self.plugins is None:
			self.plugins = Plugins(self, blacklist=plugins_blacklist, whitelist=plugins_whitelist)
			i_loaded_plugins = True
		
			if self.load_plugins:
				self.plugins._load_plugins()

		# Invoke any pre-scan plugins
		plugret_start = self.plugins._pre_scan_callbacks(fd)
		
		# Load the default signatures if self.load_signatures has not already been invoked
		if self.magic is None:
			self.load_signatures()

		# Main loop, scan through all the data
		while not ((plugret | plugret_start) & PLUGIN_TERMINATE):
			i = 0

			# Read in the next block of data from the target file and make sure it's valid
			(data, dlen) = fd.read_block()
			if not data or dlen == 0:
				break

			# The total number of bytes scanned could be bigger than the total number
			# of bytes read from the file if the previous signature result specified a 
			# jump offset that was beyond the end of the then current data block.
			#
			# If this is the case, we need to index into this data block appropriately in order to 
			# resume the scan from the appropriate offset.
			#
			# Don't update dlen though, as it is the literal offset into the data block that we
			# are to scan up to in this loop iteration. It is also appended to self.total_scanned,
			# which is what we want (even if we have been told to skip part of the block, the skipped
			# part is still considered part of the total bytes scanned).
			if jump_offset > 0:
				total_check = self.total_scanned + dlen

				# Is the jump offset beyond the total amount of data that we've currently read in (i.e., in a future data block)?
				if jump_offset >= total_check:
					i = -1
					
					# Try to seek to the jump offset; this won't work if fd == sys.stdin
					try:
						fd.seek(jump_offset)
						self.total_read = jump_offset
						self.total_scanned = jump_offset - dlen
					except:
						pass

				# Is the jump offset inside this block of data?
				elif jump_offset > self.total_scanned and jump_offset < total_check:
					# Index into this block appropriately; jump_offset is the file offset that
					# we need to jump to, and self.total_scanned is the file offset that starts
					# the beginning of the current block
					i = jump_offset - self.total_scanned

				# We're done with jump_offset, zero it out for the next round
				jump_offset = 0

			# Scan through each block of data looking for signatures
			if i >= 0 and i < dlen:

				# Scan this data block for a list of offsets which are candidates for possible valid signatures.
				# Signatures could be split across the block boundary; since data conatins 1KB more than dlen,
				# pass up to dlen+MAX_SIGNATURE_SIZE to find_signature_candidates, but don't accept signatures that 
				# start after the end of dlen.
				for candidate in self.parser.find_signature_candidates(data[i:dlen+self.MAX_SIGNATURE_SIZE], (dlen-i)):

					# If a previous signature specified a jump offset beyond this candidate signature offset, ignore it
					if (i + candidate + self.total_scanned) < jump_offset:
						continue

					# Reset these values on each loop	
					smart = {}
					results = []
					results_offset = -1

					# In python3 we need a bytes object to pass to magic.buffer
					candidate_data = str2bytes(data[i+candidate:i+candidate+fd.MAX_TRAILING_SIZE])

					# Pass the data to libmagic, and split out multiple results into a list
					for magic_result in self.parser.split(self.magic.buffer(candidate_data)):

						i_set_results_offset = False

						# Some signatures need to take into account the length of a given string
						# when specifying additional offsets. Parse the string-len keyword to adjust
						# for this prior to calling self.smart.parse.
						magic_result = self.smart._parse_string_len(magic_result)

						# Some file names are not NULL byte terminated, but rather their length is
						# specified in a size field. To ensure these are not marked as invalid due to
						# non-printable characters existing in the file name, parse the filename(s) and
						# trim them to the specified filename length, if one was specified.
						magic_result = self.smart._parse_raw_strings(magic_result)

						# Invoke any pre-parser callback plugin functions
						if not (plugret_start & PLUGIN_STOP_PLUGINS):
							raw_result = {'description' : magic_result}
							plugret = self.plugins._scan_pre_parser_callbacks(raw_result)
							magic_result = raw_result['description']
							if (plugret & PLUGIN_TERMINATE):
								break
	
						# Make sure this is a valid result before further processing
						if not self.filter.invalid(magic_result):
							# The smart filter parser returns a dictionary of keyword values and the signature description.
							smart = self.smart.parse(magic_result)

							# Validate the jump value and check if the response description should be displayed
							if self._is_valid(smart, candidate+i, fsize):
								# If multiple results are returned and one of them has smart['jump'] set to a non-zero value,
								# the calculated results offset will be wrong since i will have been incremented. Only set the
								# results_offset value when the first match is encountered.
								if results_offset < 0:
									results_offset = offset + i + candidate + smart['adjust'] + self.total_scanned
									i_set_results_offset = True

								# Double check to make sure the smart['adjust'] value is sane. 
								# If it makes results_offset negative, then it is not sane.
								if results_offset >= 0:
									smart['offset'] = results_offset

									# Invoke any scan plugins 
									if not (plugret_start & PLUGIN_STOP_PLUGINS):
										plugret = self.plugins._scan_callbacks(smart)
										results_offset = smart['offset']
										if (plugret & PLUGIN_TERMINATE):
											break

									# Extract the result, if it matches one of the extract rules and is not a delayed extract.
									if self.extractor.enabled and not (self.extractor.delayed and smart['delay']) and not ((plugret | plugret_start) & PLUGIN_NO_EXTRACT):
										# If the signature did not specify a size, extract to the end of the file.
										if not smart['size']:
											smart['size'] = fsize-results_offset
										
										smart['extract'] = self.extractor.extract(	results_offset, 
																smart['description'], 
																target_file, 
																smart['size'], 
																name=smart['name'])

									if not ((plugret | plugret_start) & PLUGIN_NO_DISPLAY):
										# This appears to be a valid result, so append it to the results list.
										results.append(smart)
									elif i_set_results_offset:
										results_offset = -1

					# Did we find any valid results?
					if results_offset >= 0:
						scan_results[results_offset] = results
					
						if callback is not None:
							callback(results_offset, results)
			
						# If a relative jump offset was specified, update the absolute jump_offset variable
						if has_key(smart, 'jump') and smart['jump'] > 0:
							jump_offset = results_offset + smart['jump']

			# Track the total number of bytes scanned
			self.total_scanned += dlen
			# The starting offset only affects the reported offset for results
			# in the first block of data. Zero it out after the first block has
			# been processed.
			offset = 0

		# Sort the results before returning them
		scan_items = list(scan_results.items())
		scan_items.sort()

		# Do delayed extraction, if specified.
		if self.extractor.enabled and self.extractor.delayed:
			scan_items = self.extractor.delayed_extract(scan_items, target_file, fsize)

		# Invoke any post-scan plugins
		#if not (plugret_start & PLUGIN_STOP_PLUGINS):
		self.plugins._post_scan_callbacks(fd)

		# Be sure to delete the Plugins instance so that there isn't a lingering reference to
		# this Binwalk class instance (lingering handles to this Binwalk instance cause the
		# __del__ deconstructor to not be called).
		if i_loaded_plugins:
			del self.plugins
			self.plugins = None

		if i_opened_fd:
			fd.close()

		return scan_items

	def concatenate_results(self, results, new):
		'''
		Concatenate multiple Binwalk.scan results into one dictionary.

		@results - Binwalk results to append new results to.
		@new     - New data to append to results.

		Returns None.
		'''
		for (new_file_name, new_data) in iterator(new):
			if not has_key(results, new_file_name):
				results[new_file_name] = new_data
			else:
				for i in range(0, len(new_data)):
					found_offset = False
					(new_offset, new_results_list) = new_data[i]

					for j in range(0, len(results[new_file_name])):
						(offset, results_list) = results[new_file_name][j]
						if offset == new_offset:
							results_list += new_results_list
							results[new_file_name][j] = (offset, results_list)
							found_offset = True
							break
					
					if not found_offset:
						results[new_file_name] += new_data

	def _is_valid(self, result, location, file_size):
		'''
		Determines if a result string is valid and should be displayed to the user or not.
		
		@result    - Result dictionary, as returned by self.smart.parse.
		@location  - The file offset of the result.
		@file_size - The total size of the file.

		Returns True if the string should be displayed.
		Returns False if the string should not be displayed.
		'''
		if self.filter.show_invalid_results:
			return True

		if result['invalid'] or result['jump'] < 0 or result['size'] < 0:
			return False
		if ((location + result['size']) > file_size) or (self.year and result['year'] > self.year) or (self.epoch and result['epoch'] > self.epoch):
			return False

		desc = result['description']
		return (desc and desc is not None and not self.filter.invalid(desc) and self.filter.filter(desc) != self.filter.FILTER_EXCLUDE)

