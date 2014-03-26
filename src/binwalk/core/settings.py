# Code for loading and accessing binwalk settings (extraction rules, signature files, etc).

import os
import binwalk.core.common as common
from binwalk.core.compat import *

class Settings:
    '''
    Binwalk settings class, used for accessing user and system file paths and general configuration settings.
    
    After instatiating the class, file paths can be accessed via the self.paths dictionary.
    System file paths are listed under the 'system' key, user file paths under the 'user' key.

    Valid file names under both the 'user' and 'system' keys are as follows:

        o BINWALK_MAGIC_FILE  - Path to the default binwalk magic file.
        o PLUGINS             - Path to the plugins directory.
    '''
    # Release version
    VERSION = "2.0.0 beta"

    # Sub directories
    BINWALK_USER_DIR = ".binwalk"
    BINWALK_MAGIC_DIR = "magic"
    BINWALK_CONFIG_DIR = "config"
    BINWALK_PLUGINS_DIR = "plugins"

    # File names
    PLUGINS = "plugins"
    EXTRACT_FILE = "extract.conf"
    BINWALK_MAGIC_FILE = "binwalk"
    BINARCH_MAGIC_FILE = "binarch"
    BINCAST_MAGIC_FILE = "bincast"

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
            'user'      : {},
            'system'    : {},
        }

        # Build the paths to all user-specific files
        self.paths['user'][self.BINWALK_MAGIC_FILE] = self._user_path(self.BINWALK_MAGIC_DIR, self.BINWALK_MAGIC_FILE)
        self.paths['user'][self.BINARCH_MAGIC_FILE] = self._user_path(self.BINWALK_MAGIC_DIR, self.BINARCH_MAGIC_FILE)
        self.paths['user'][self.BINCAST_MAGIC_FILE] = self._user_path(self.BINWALK_MAGIC_DIR, self.BINCAST_MAGIC_FILE)
        self.paths['user'][self.EXTRACT_FILE] = self._user_path(self.BINWALK_CONFIG_DIR, self.EXTRACT_FILE)
        self.paths['user'][self.PLUGINS] = self._user_path(self.BINWALK_PLUGINS_DIR)

        # Build the paths to all system-wide files
        self.paths['system'][self.BINWALK_MAGIC_FILE] = self._system_path(self.BINWALK_MAGIC_DIR, self.BINWALK_MAGIC_FILE)
        self.paths['system'][self.BINARCH_MAGIC_FILE] = self._system_path(self.BINWALK_MAGIC_DIR, self.BINARCH_MAGIC_FILE)
        self.paths['system'][self.BINCAST_MAGIC_FILE] = self._system_path(self.BINWALK_MAGIC_DIR, self.BINCAST_MAGIC_FILE)
        self.paths['system'][self.EXTRACT_FILE] = self._system_path(self.BINWALK_CONFIG_DIR, self.EXTRACT_FILE)
        self.paths['system'][self.PLUGINS] = self._system_path(self.BINWALK_PLUGINS_DIR)

    def get_file_path(self, usersys, fname):
        '''
        Retrieves the specified file path from self.paths.

        @usersys - One of: 'user', 'system'.
        @fname   - The file name (e.g., self.BINWALK_MAGIC_FILE, self.PLUGINS, etc)

        Returns the path, if it exists; returns None otherwise.
        '''
        if self.paths.has_key(usersys) and has_key(self.paths[usersys], fname) and self.paths[usersys][fname]:
            return self.paths[usersys][fname]
        return None

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
            return os.path.dirname(os.path.dirname(os.path.abspath(root)))
        except KeyboardInterrupt as e:
            raise e
        except Exception:
            return ''

    def _get_user_dir(self):
        '''
        Get the user's home directory.
        '''
        try:
            # This should work in both Windows and Unix environments
            return os.getenv('USERPROFILE') or os.getenv('HOME')
        except KeyboardInterrupt as e:
            raise e
        except Exception:
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
            except KeyboardInterrupt as e:
                raise e
            except Exception:
                pass
        
        fpath = os.path.join(dirname, filename)

        if not os.path.exists(fpath):
            try:
                open(fpath, "w").close()
            except KeyboardInterrupt as e:
                raise e
            except Exception:
                pass

        return fpath

    def _user_path(self, subdir, basename=''):
        '''
        Gets the full path to the 'subdir/basename' file in the user binwalk directory.

        @subdir   - Subdirectory inside the user binwalk directory.
        @basename - File name inside the subdirectory.

        Returns the full path to the 'subdir/basename' file.
        '''
        try:
            return self._file_path(os.path.join(self.user_dir, self.BINWALK_USER_DIR, subdir), basename)
        except KeyboardInterrupt as e :
            raise e
        except Exception:
            return None

    def _system_path(self, subdir, basename=''):
        '''
        Gets the full path to the 'subdir/basename' file in the system binwalk directory.
        
        @subdir   - Subdirectory inside the system binwalk directory.
        @basename - File name inside the subdirectory.
        
        Returns the full path to the 'subdir/basename' file.
        '''
        try:
            return self._file_path(os.path.join(self.system_dir, subdir), basename)
        except KeyboardInterrupt as e :
            raise e
        except Exception:
            return None

