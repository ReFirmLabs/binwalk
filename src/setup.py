#!/usr/bin/env python
from __future__ import print_function
import os
import sys
import subprocess
from os import listdir, path
from distutils.core import setup

# Python2/3 compliance
try:
	raw_input
except:
	raw_input = input

# This is super hacky.
if "--yes" in sys.argv:
	sys.argv.pop(sys.argv.index("--yes"))
	IGNORE_WARNINGS = True
else:
	IGNORE_WARNINGS = False

def which(fname):
	cmd = ["which", fname]
	return subprocess.Popen(cmd, stdout=subprocess.PIPE).stdout.readline().strip()

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
		
print("checking pre-requisites")
try:
	import magic
	try:
		magic.MAGIC_NO_CHECK_TEXT
	except Exception as e:
		msg = ["Pre-requisite failure: " + str(e),
			"It looks like you have an old or incompatible magic module installed.",
			"Please install the official python-magic module, or download and install it from source: ftp://ftp.astron.com/pub/file/"
		]
		
		warning(msg)
except Exception as e:
	msg = ["Pre-requisite failure:", str(e),
		"Please install the python-magic module, or download and install it from source: ftp://ftp.astron.com/pub/file/",
	]
	
	warning(msg)

try:
	import pyqtgraph
except Exception as e:
	msg = ["Pre-requisite check warning: " + str(e),
		"To take advantage of this tool's graphing capabilities, please install the pyqtgraph module.",
	]
	
	warning(msg, prompt=True)

# Build / install C compression libraries
c_lib_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "C")
c_lib_makefile = os.path.join(c_lib_dir, "Makefile")

working_directory = os.getcwd()
os.chdir(c_lib_dir)
status = 0

if not os.path.exists(c_lib_makefile):
	status |= os.system("./configure")

status |= os.system("make")

if status != 0:
	msg = ["Build warning: failed to build compression libraries.",
		"Some plugins will not work without these libraries."
	]
	
	warning(msg, prompt=True)
else:
	if "install" in sys.argv:
		if os.system("make install") != 0:
			msg = ["Install warning: failed to install compression libraries.",
				"Some plugins will not work without these libraries."
			]

			warning(msg, prompt=True)
		
os.chdir(working_directory)

# Generate a new magic file from the files in the magic directory
print("generating binwalk magic file")
magic_files = listdir("magic")
magic_files.sort()
fd = open("binwalk/magic/binwalk", "wb")
for magic in magic_files:
	fpath = path.join("magic", magic)
	if path.isfile(fpath):
		data = open(fpath).read()
		try:
			fd.write(data)
		except TypeError:
			fd.write(bytes(data, 'UTF-8'))
fd.close()

# The data files to install along with the binwalk module
install_data_files = ["magic/*", "config/*", "plugins/*"]

# Install the binwalk module, script and support files
setup(	name = "binwalk",
	version = "1.2.3",
	description = "Firmware analysis tool",
	author = "Craig Heffner",
	url = "https://github.com/devttys0/binwalk",

	requires = ["magic", "matplotlib.pyplot"],	
	packages = ["binwalk"],
	package_data = {"binwalk" : install_data_files},
	scripts = ["bin/binwalk"],
)

