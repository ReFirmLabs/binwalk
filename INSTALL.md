Before You Start
================

Binwalk supports Python 2.7 - 3.x. Although binwalk is slightly faster in Python 3, the Python OpenGL bindings are still experimental for Python 3, so Python 2.7 is recommended.

The following installation procedures assume that you are installing binwalk to be run using Python 2.7. If you want to use binwalk in Python 3, some package
names and installation procedures may differ slightly.

Installation
============

Installation follows the typical configure/make process (standard development tools such as gcc, make, and Python must be installed in order to build):

```bash
$ ./configure
$ make
$ sudo make install
```

Binwalk's core features will work out of the box without any additional dependencies. However, to take advantage of binwalk's more advanced capabilities, multiple supporting utilities/packages need to be installed (see the Dependencies section below).

Dependencies
============

The following run-time dependencies are only required for optional binwalk features, such as file extraction and graphing capabilities. Unless otherwise specified, these dependencies are available from most Linux package managers.

Binwalk uses [pyqtgraph](http://www.pyqtgraph.org) to generate graphs and visualizations, which requires the following: 

```bash
$ sudo apt-get install libqt4-opengl python-opengl python-qt4 python-qt4-gl python-numpy python-scipy
$ sudo pip install pyqtgraph
```

Binwalk's "Fuzzy Hashing" options require the libfuzzy library:

```bash
$ sudo apt-get install libfuzzy2
```

Binwalk's `--disasm` option requires the [Capstone](http://www.capstone-engine.org/) disassembly framework and its corresponding Python bindings:

```bash
$ wget http://www.capstone-engine.org/download/2.1.2/capstone-2.1.2.tgz
$ tar -zxvf capstone-2.1.2.tgz
$ (cd capstone-2.1.2 && ./make.sh && sudo make install)
$ (cd capstone-2.1.2/bindings/python && sudo python ./setup.py install)
```

Binwalk relies on multiple external utilties in order to automatically extract/decompress files and data:

```bash
$ sudo apt-get install mtd-utils zlib1g-dev liblzma-dev ncompress gzip bzip2 tar arj p7zip p7zip-full cabextract openjdk-6-jdk
```

```bash
$ git clone https://github.com/devttys0/sasquatch
$ (cd sasquatch && make && sudo make install)
```

Bundled Software
================

For convenience, the following libraries are bundled with binwalk and installed so as not to conflict with system-wide libraries:

    libmagic

Installation of any individual bundled library can be disabled at build time:

```bash
$ ./configure --disable-libmagic
```

Alternatively, installation of all bundled libraries can be disabled at build time:

```bash
$ ./configure --disable-bundles
```

If a bundled library is disabled, the equivalent library must be installed to a standard system library location (e.g., `/usr/lib`, `/usr/local/lib`, etc) in order for binwalk to find it at run time.

**Note:** If the bundled libmagic library is not used, be aware that:

1. Some versions of libmagic have known bugs that are triggered by binwalk under some circumstances.
2. Minor version releases of libmagic may not be backwards compatible with each other and installation of the wrong version of libmagic may cause binwalk to fail to function properly. 
3. Conversely, updating libmagic to a version that works with binwalk may cause other utilities that rely on libmagic to fail. 

Currently, the following libmagic versions are known to work properly with binwalk (other versions may or may not work):

    5.18
    5.19


Specifying a Python Interpreter
===============================

The default python interpreter used during install is the system-wide `python` interpreter. A different interpreter (e.g., `python2`, `python3`) can be specified at build time:

```bash
$ ./configure --with-python=python3
```


Installing the IDA Plugin
=========================

If IDA is installed on your system, you may optionally install the IDA plugin by specifying the location of your IDA install directory at build time:

```bash
$ ./configure --with-ida=/home/user/ida-6.6
$ make ida
```

Uninstallation
==============

The following command will remove binwalk from your system. Note that this will *not* remove manually installed packages or tools:

```bash
$ sudo make uninstall
```

