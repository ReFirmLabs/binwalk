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

# This is super hacky.
if "--yes" in sys.argv:
	sys.argv.pop(sys.argv.index("--yes"))
	IGNORE_WARNINGS = True
else:
	IGNORE_WARNINGS = False

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

def warning(lines, terminate=True, prompt=True):
	WIDTH = 115

	if not IGNORE_WARNINGS:
		print("\n" + "*" * WIDTH)
		for line in lines:
			print(line)
		print("*" * WIDTH, "\n")

		if prompt:
			if raw_input('Continue installation anyway (Y/n)? ').lower().startswith('n'):
				terminate = True
			else:
				terminate = False

		if terminate:
			sys.exit(1)

class UninstallCommand(Command):
	description = "Uninstalls the Python module"
	user_options = []

	def initialize_options(self):
		pass

	def finalize_options(self):
		pass

	def run(self):
		try:
			import binwalk
			for path in binwalk.__path__:
				try:
					remove_tree(path)
				except OSError as e:
					pass
		except KeyboardInterrupt as e:
			raise e
		except Exception as e:
			pass

		script_path = which(MODULE_NAME)
		if script_path:
			try:
				print("removing '%s'" % script_path)
				os.unlink(script_path)
			except KeyboardInterrupt as e:
				pass
			except Exception as e:
				pass

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

# Check pre-requisite Python modules during an install
if "install" in sys.argv:
	print("checking pre-requisites")
	try:
		import pyqtgraph
		from pyqtgraph.Qt import QtCore, QtGui, QtOpenGL
	except ImportError as e:
		msg = ["Pre-requisite warning: " + str(e),
			   "To take advantage of %s's graphing capabilities, please install this module." % MODULE_NAME,
		]
	
		warning(msg, prompt=True)

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
install_data_files = ["magic/*", "config/*", "plugins/*", "modules/*", "core/*"]

# Install the module, script, and support files
setup(name = MODULE_NAME,
	  version = "2.0.0 beta",
	  description = "Firmware analysis tool",
	  author = "Craig Heffner",
	  url = "https://github.com/devttys0/%s" % MODULE_NAME,

	  requires = ["magic", "pyqtgraph"],
	  packages = [MODULE_NAME],
	  package_data = {MODULE_NAME : install_data_files},
	  scripts = [os.path.join("scripts", MODULE_NAME)],

	  cmdclass = {'clean' : CleanCommand, 'uninstall' : UninstallCommand}
)

