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
            os.remove("%s/magic/%s" % (MODULE_NAME, MODULE_NAME))
        except Exception:
            pass

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

if "install" in sys.argv:
    # If an older version of binwalk is currently installed, completely remove it to prevent conflicts
    existing_binwalk_modules = find_binwalk_module_paths()
    if existing_binwalk_modules and not os.path.exists(os.path.join(existing_binwalk_modules[0], "core")):
        remove_binwalk_module()

# Re-build the magic file during a build/install
if "install" in sys.argv or "build" in sys.argv:
    # Generate a new magic file from the files in the magic directory
    print("creating %s magic file" % MODULE_NAME)
    magic_files = os.listdir("magic")
    magic_files.sort()
    fd = open("%s/magic/%s" % (MODULE_NAME, MODULE_NAME), "wb")
    for magic in magic_files:
        fpath = os.path.join("magic", magic)
        if os.path.isfile(fpath):
            fd.write(open(fpath, "rb").read())
    fd.close()

# The data files to install along with the module
data_dirs = ["magic", "config", "plugins", "modules", "core"]
install_data_files = [os.path.join("libs", "*.so"), os.path.join("libs", "*.dylib")]

for data_dir in data_dirs:
    install_data_files.append("%s%s*" % (data_dir, os.path.sep))

if os.getenv("BUILD_PYQTGRAPH") == "yes":
    install_data_files.append(os.path.join("libs", "pyqtgraph", "*.py"))

    for (root, dirs, files) in os.walk(os.path.join(MODULE_NAME, "libs", "pyqtgraph")):
        if dirs:
            for directory in dirs:
                install_data_files.append(os.path.join(os.path.sep.join(root.split(os.path.sep)[1:]), os.path.join(directory, "*.py")))

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

