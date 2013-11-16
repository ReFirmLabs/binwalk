#!/usr/bin/env python
import os
import sys
import subprocess
from os import listdir, path
from distutils.core import setup

WIDTH = 115

def which(fname):
	cmd = ["which", fname]
	return subprocess.Popen(cmd, stdout=subprocess.PIPE).stdout.readline().strip()

# Check for pre-requisite modules only if --no-prereq-checks was not specified
if "--no-prereq-checks" not in sys.argv:
	print "checking pre-requisites"
	try:
		import magic
		try:
			magic.MAGIC_NO_CHECK_TEXT
		except Exception, e:
			print "\n", "*" * WIDTH
			print "Pre-requisite failure:", str(e)
			print "It looks like you have an old or incompatible magic module installed."
			print "Please install the official python-magic module, or download and install it from source: ftp://ftp.astron.com/pub/file/"
			print "*" * WIDTH, "\n"
			sys.exit(1)
	except Exception, e:
		print "\n", "*" * WIDTH
		print "Pre-requisite failure:", str(e)
		print "Please install the python-magic module, or download and install it from source: ftp://ftp.astron.com/pub/file/"
		print "*" * WIDTH, "\n"
		sys.exit(1)

	try:
		import matplotlib
		matplotlib.use('Agg')
		import matplotlib.pyplot
		import numpy
	except Exception, e:
		print "\n", "*" * WIDTH
		print "Pre-requisite check warning:", str(e)
		print "To take advantage of this tool's entropy plotting capabilities, please install the python-matplotlib module."
		print "*" * WIDTH, "\n"
	
		if raw_input('Continue installation without this module (Y/n)? ').lower().startswith('n'):
			print 'Quitting...\n'
			sys.exit(1)
else:
	# This is super hacky.
	sys.argv.pop(sys.argv.index("--no-prereq-checks"))

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
	print "ERROR: Failed to build libtinfl.so! Do you have gcc installed?"
	sys.exit(1)

if "install" in sys.argv:
	os.system("make install")

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

