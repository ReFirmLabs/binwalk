#!/usr/bin/env python
import os
import sys
import subprocess
from os import listdir, path
from distutils.core import setup

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
		print "\n", "*" * WIDTH
		for line in lines:
			print line
		print "*" * WIDTH, "\n"

		if prompt:
			if raw_input('Continue installation anyway (Y/n)? ').lower().startswith('n'):
				terminate = True
			else:
				terminate = False

		if terminate:
			sys.exit(1)
		
# Check for pre-requisite modules only if --no-prereq-checks was not specified
print "checking pre-requisites"
try:
	import magic
	try:
		magic.MAGIC_NO_CHECK_TEXT
	except Exception, e:
		msg = ["Pre-requisite failure:", str(e),
			"It looks like you have an old or incompatible magic module installed.",
			"Please install the official python-magic module, or download and install it from source: ftp://ftp.astron.com/pub/file/"
		]
		
		warning(msg)
except Exception, e:
	msg = ["Pre-requisite failure:", str(e),
		"Please install the python-magic module, or download and install it from source: ftp://ftp.astron.com/pub/file/",
	]
	
	warning(msg)

try:
	import matplotlib
	matplotlib.use('Agg')
	import matplotlib.pyplot
	import numpy
except Exception, e:
	msg = ["Pre-requisite check warning:", str(e),
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
	msg = ["Failed to build compression libraries.",
		"Some plugins will not work without these libraries."
	]
	
	warning(msg, prompt=True)
else:
	if "install" in sys.argv:
		if os.system("make install") != 0:
			msg = ["Failed to install compression libraries.",
				"Some plugins will not work without these libraries."
			]

			warning(msg, prompt=True)
		
os.chdir(working_directory)

# Generate a new magic file from the files in the magic directory
print "generating binwalk magic file"
magic_files = listdir("magic")
magic_files.sort()
fd = open("binwalk/magic/binwalk", "wb")
for magic in magic_files:
	fpath = path.join("magic", magic)
	if path.isfile(fpath):
		fd.write(open(fpath).read())
fd.close()

# The data files to install along with the binwalk module
install_data_files = ["magic/*", "config/*", "plugins/*"]

# Install the binwalk module, script and support files
setup(	name = "binwalk",
	version = "1.2.3",
	description = "Firmware analysis tool",
	author = "Craig Heffner",
	url = "http://binwalk.googlecode.com",

	requires = ["magic", "matplotlib.pyplot"],	
	packages = ["binwalk"],
	package_data = {"binwalk" : install_data_files},
	scripts = ["bin/binwalk"],
)

# If python2 exists, replace the shebang to invoke python2.
# This prevents python3 from being used when running binwalk.
# This shouldn't be done on the ./bin/binwalk file, as that would
# cause a conflict between the master branch and the local clone.
python2_path = which("python2")
binwalk_path = which("binwalk")

if python2_path and binwalk_path:
	i = 0
	data = ''

	for line in open(binwalk_path, 'rb').readlines():
		if i == 0:
			line = "#!/usr/bin/env python2\n"
		data += line
		i += 1

	open(binwalk_path, 'wb').write(data)

