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

def warning(lines, terminate=True, prompt=False):
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
	import matplotlib
	matplotlib.use('Agg')
	import matplotlib.pyplot
	import numpy
except Exception as e:
	msg = ["Pre-requisite check warning: " + str(e),
		"To take advantage of this tool's entropy plotting capabilities, please install the python-matplotlib module.",
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

# If the bash auto-completion directory exists, generate an auto-completion file
bash_completion_dir = os.path.join('/', 'etc', 'bash_completion.d')

if os.path.exists(bash_completion_dir):
	import binwalk.cmdopts

	print("Installing bash auto-completion file")

	long_opts_key = '%%LONG_OPTS%%'
	short_opts_key = '%%SHORT_OPTS%%'
	file_opts_key = '%%FILE_OPTS%%'
	file_name_in = 'binwalk.completion'
	file_name_out = os.path.join(bash_completion_dir, 'binwalk')

	long_opts = []
	short_opts = []
	file_opts = ['--file=', '--extract=', '--magic=']

	for opt in binwalk.cmdopts.short_options:
		if opt != ':':
			short_opts.append('-' + opt)

	for opt in binwalk.cmdopts.long_options:
		long_opts.append('--' + opt)

	try:
		with open(file_name_in) as fd_in:
			with open(file_name_out, 'w') as fd_out:
				for line in fd_in.readlines():
					if long_opts_key in line:
						line = line.replace(long_opts_key, ' '.join(long_opts))
					elif short_opts_key in line:
						line = line.replace(short_opts_key, ' '.join(short_opts))
					elif file_opts_key in line:
						line = line.replace(file_opts_key, ' '.join(file_opts))
	
					fd_out.write(line)
	except Exception as e:
		print("WARNING: Failed to install auto-completion file: %s" % e)
		try:
			os.unlink(file_name_out)
		except:
			pass

