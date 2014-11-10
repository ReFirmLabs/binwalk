#!/usr/bin/env python
from __future__ import print_function
import os
import sys
import tempfile
import subprocess
from distutils.core import setup, Command
from distutils.dir_util import remove_tree

MODULE_NAME = "binwalk"

# Python2/3 compliance
try:
    raw_input
except NameError:
    raw_input = input

# cd into the src directory, no matter where setup.py was invoked from
os.chdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), "src"))

def which(command):
    # /usr/local/bin is usually the default install path, though it may not be in $PATH
    usr_local_bin = os.path.sep.join([os.path.sep, 'usr', 'local', 'bin', command])

    try:
        location = subprocess.Popen(["which", command], shell=False, stdout=subprocess.PIPE).communicate()[0].strip()
    except KeyboardInterrupt as e:
        raise e
    except Exception as e:
        pass

    if not location and os.path.exists(usr_local_bin):
        location = usr_local_bin

    return location

def find_binwalk_module_paths():
    paths = []

    try:
        import binwalk
        paths = binwalk.__path__
    except KeyboardInterrupt as e:
        raise e
    except Exception:
        pass

    return paths

def remove_binwalk_module(pydir=None, pybin=None):
    if pydir:
        module_paths = [pydir]
    else:
        module_paths = find_binwalk_module_paths()

    for path in module_paths:
        try:
            remove_tree(path)
        except OSError as e:
            pass

    if not pybin:
        pybin = which(MODULE_NAME)

    if pybin:
        try:
            print("removing '%s'" % pybin)
            os.unlink(pybin)
        except KeyboardInterrupt as e:
            pass
        except Exception as e:
            pass

class UninstallCommand(Command):
    description = "Uninstalls the Python module"
    user_options = [
                    ('pydir=', None, 'Specify the path to the binwalk python module to be removed.'),
                    ('pybin=', None, 'Specify the path to the binwalk executable to be removed.'),
    ]

    def initialize_options(self):
        self.pydir = None
        self.pybin = None

    def finalize_options(self):
        pass

    def run(self):
        remove_binwalk_module(self.pydir, self.pybin)

class CleanCommand(Command):
    description = "Clean Python build directories"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            remove_tree("build")
        except KeyboardInterrupt as e:
            raise e
        except Exception:
            pass

        try:
            remove_tree("dist")
        except KeyboardInterrupt as e:
            raise e
        except Exception:
            pass

# The data files to install along with the module
install_data_files = []
for data_dir in ["magic", "config", "plugins", "modules", "core"]:
        install_data_files.append("%s%s*" % (data_dir, os.path.sep))

# Install the module, script, and support files
setup(name = MODULE_NAME,
      version = "2.1.0",
      description = "Firmware analysis tool",
      author = "Craig Heffner",
      url = "https://github.com/devttys0/%s" % MODULE_NAME,

      requires = [],
      packages = [MODULE_NAME],
      package_data = {MODULE_NAME : install_data_files},
      scripts = [os.path.join("scripts", MODULE_NAME)],

      cmdclass = {'clean' : CleanCommand, 'uninstall' : UninstallCommand}
)

