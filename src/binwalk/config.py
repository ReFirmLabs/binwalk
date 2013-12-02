import os
import binwalk.common as common
from binwalk.compat import *

class Config:
	'''
	Binwalk configuration class, used for accessing user and system file paths.
	
	After instatiating the class, file paths can be accessed via the self.paths dictionary.
	System file paths are listed under the 'system' key, user file paths under the 'user' key.

	For example, to get the path to both the user and system binwalk magic files:

		from binwalk import Config

		conf = Config()
		user_binwalk_file = conf.paths['user'][conf.BINWALK_MAGIC_FILE]
		system_binwalk_file = conf.paths['system'][conf.BINWALK_MAGIC_FILE]

	There is also an instance of this class available via the Binwalk.config object:

		import binwalk

		bw = binwalk.Binwalk()

		user_binwalk_file = bw.config.paths['user'][conf.BINWALK_MAGIC_FILE]
		system_binwalk_file = bw.config.paths['system'][conf.BINWALK_MAGIC_FILE]

	Valid file names under both the 'user' and 'system' keys are as follows:

		o BINWALK_MAGIC_FILE  - Path to the default binwalk magic file.
		o BINCAST_MAGIC_FILE  - Path to the bincast magic file (used when -C is specified with the command line binwalk script).
		o BINARCH_MAGIC_FILE  - Path to the binarch magic file (used when -A is specified with the command line binwalk script).
		o EXTRACT_FILE        - Path to the extract configuration file (used when -e is specified with the command line binwalk script).
		o PLUGINS             - Path to the plugins directory.
	'''
	# Release version
	VERSION = "1.3.0 beta"

	# Sub directories
	BINWALK_USER_DIR = ".binwalk"
	BINWALK_MAGIC_DIR = "magic"
	BINWALK_CONFIG_DIR = "config"
	BINWALK_PLUGINS_DIR = "plugins"

	# File names
	PLUGINS = "plugins"
	EXTRACT_FILE = "extract.conf"
	BINWALK_MAGIC_FILE = "binwalk"
	BINCAST_MAGIC_FILE = "bincast"
	BINARCH_MAGIC_FILE = "binarch"
	ZLIB_MAGIC_FILE = "zlib"
	COMPRESSD_MAGIC_FILE = "compressd"

	def __init__(self):
		'''
		Class constructor. Enumerates file paths and populates self.paths.
		'''
		# Path to the user binwalk directory
		self.user_dir = self._get_user_dir()
		# Path to the system wide binwalk directory
		self.system_dir = self._get_system_dir()

		# Dictionary of all absolute user/system file paths
		self.paths = {
			'user'		: {},
			'system'	: {},
		}

		# Build the paths to all user-specific files
		self.paths['user'][self.BINWALK_MAGIC_FILE] = self._user_path(self.BINWALK_MAGIC_DIR, self.BINWALK_MAGIC_FILE)
		self.paths['user'][self.BINCAST_MAGIC_FILE] = self._user_path(self.BINWALK_MAGIC_DIR, self.BINCAST_MAGIC_FILE)
		self.paths['user'][self.BINARCH_MAGIC_FILE] = self._user_path(self.BINWALK_MAGIC_DIR, self.BINARCH_MAGIC_FILE)
		self.paths['user'][self.EXTRACT_FILE] = self._user_path(self.BINWALK_CONFIG_DIR, self.EXTRACT_FILE)
		self.paths['user'][self.PLUGINS] = self._user_path(self.BINWALK_PLUGINS_DIR)

		# Build the paths to all system-wide files
		self.paths['system'][self.BINWALK_MAGIC_FILE] = self._system_path(self.BINWALK_MAGIC_DIR, self.BINWALK_MAGIC_FILE)
		self.paths['system'][self.BINCAST_MAGIC_FILE] = self._system_path(self.BINWALK_MAGIC_DIR, self.BINCAST_MAGIC_FILE)
		self.paths['system'][self.BINARCH_MAGIC_FILE] = self._system_path(self.BINWALK_MAGIC_DIR, self.BINARCH_MAGIC_FILE)
		self.paths['system'][self.ZLIB_MAGIC_FILE] = self._system_path(self.BINWALK_MAGIC_DIR, self.ZLIB_MAGIC_FILE)
		self.paths['system'][self.COMPRESSD_MAGIC_FILE] = self._system_path(self.BINWALK_MAGIC_DIR, self.COMPRESSD_MAGIC_FILE)
		self.paths['system'][self.EXTRACT_FILE] = self._system_path(self.BINWALK_CONFIG_DIR, self.EXTRACT_FILE)
		self.paths['system'][self.PLUGINS] = self._system_path(self.BINWALK_PLUGINS_DIR)

	def find_magic_file(self, fname, system_only=False, user_only=False):
		'''
		Finds the specified magic file name in the system / user magic file directories.

		@fname       - The name of the magic file.
		@system_only - If True, only the system magic file directory will be searched.
		@user_only   - If True, only the user magic file directory will be searched.

		If system_only and user_only are not set, the user directory is always searched first.

		Returns the path to the file on success; returns None on failure.
		'''
		loc = None

		if not system_only:
			fpath = self._user_path(self.BINWALK_MAGIC_DIR, fname)
			if os.path.exists(fpath) and common.file_size(fpath) > 0:
				loc = fpath

		if loc is None and not user_only:
			fpath = self._system_path(self.BINWALK_MAGIC_DIR, fname)
			if os.path.exists(fpath) and common.file_size(fpath) > 0:
				loc = fpath

		return fpath
	
	def _get_system_dir(self):
		'''
		Find the directory where the binwalk module is installed on the system.
		'''
		try:
			root = __file__
			if os.path.islink(root):
				root = os.path.realpath(root)
			return os.path.dirname(os.path.abspath(root))
		except:
			return ''

	def _get_user_dir(self):
		'''
		Get the user's home directory.
		'''
		try:
			# This should work in both Windows and Unix environments
			return os.getenv('USERPROFILE') or os.getenv('HOME')
		except:
			return ''

	def _file_path(self, dirname, filename):
		'''
		Builds an absolute path and creates the directory and file if they don't already exist.

		@dirname  - Directory path.
		@filename - File name.
		
		Returns a full path of 'dirname/filename'.
		'''
		if not os.path.exists(dirname):
			try:
				os.makedirs(dirname)
			except:
				pass
		
		fpath = os.path.join(dirname, filename)

		if not os.path.exists(fpath):
			try:
				open(fpath, "w").close()
			except:
				pass

		return fpath

	def _user_path(self, subdir, basename=''):
		'''
		Gets the full path to the 'subdir/basename' file in the user binwalk directory.

		@subdir   - Subdirectory inside the user binwalk directory.
		@basename - File name inside the subdirectory.

		Returns the full path to the 'subdir/basename' file.
		'''
		return self._file_path(os.path.join(self.user_dir, self.BINWALK_USER_DIR, subdir), basename)

	def _system_path(self, subdir, basename=''):
		'''
		Gets the full path to the 'subdir/basename' file in the system binwalk directory.
		
		@subdir   - Subdirectory inside the system binwalk directory.
		@basename - File name inside the subdirectory.
		
		Returns the full path to the 'subdir/basename' file.
		'''
		return self._file_path(os.path.join(self.system_dir, subdir), basename)

