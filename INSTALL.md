Before You Start
================

Binwalk supports Python 2.7 - 3.x. The following installation procedures assume that you are installing binwalk to be run using Python 2.7. If you want to use binwalk in Python 3, some package names and installation procedures may differ slightly.

Installation
============

Installation follows the typical configure/make process (standard development tools such as gcc, make, and Python must be installed in order to build):

```bash
$ ./configure
$ make
$ sudo make install
```

Many features will work out of the box without any additional dependencies. However, to take advantage of binwalk's more advanced capabilities, multiple supporting utilities/packages need to be installed (see the Dependencies section below).

Dependencies
============

Binwalk's only required run-time dependencies are libmagic and python-lzma:

```bash
$ sudo apt-get install libmagic1 python-lzma
```

Note that the libmagic development package is *not* required, and almost all Linux systems will already have libmagic installed. Additionally, python-lzma is a standard package in Python3, and thus requires no additional installation if running binwalk in Python3.

The remaining run-time dependencies are only required for optional binwalk features, such as file extraction and graphing capabilities. Unless otherwise specified, these dependencies are available from most Linux package managers.

Binwalk uses [pyqtgraph](http://www.pyqtgraph.org) to generate graphs and visualizations, which requires the following: 

```bash
$ sudo apt-get install libqt4-opengl python-opengl python-qt4 python-qt4-gl python-numpy python-scipy python-pip
$ sudo pip install pyqtgraph
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
# Install standard extraction utilities
$ sudo apt-get install mtd-utils zlib1g-dev liblzma-dev gzip bzip2 tar arj lhasa p7zip p7zip-full cabextract openjdk-6-jdk cramfsprogs cramfsswap squashfs-tools
```

```bash
# Install sasquatch SquashFS extraction tool and its dependencies
$ sudo apt-get install zlib1g-dev liblzma-dev liblzo2-dev
$ git clone https://github.com/devttys0/sasquatch
$ (cd sasquatch && make && sudo make install)
```

Bundled Software
================

For convenience, the following libraries are bundled with the binwalk source:

    libmagic

By default, libmagic is not built or installed unless explicitly enabled during the build process:

```bash
$ ./configure --enable-libmagic
```

By default, it is assumed that the libmagic library is already installed to a standard system library location (e.g., `/usr/lib`, `/usr/local/lib`, etc) in order for binwalk to find it at run time. 

**Note:** If the bundled libmagic library is not used, be aware that:

1. Some versions of libmagic have known bugs that are triggered by binwalk under some circumstances.
2. Minor version releases of libmagic may not be backwards compatible with each other and installation of the wrong version of libmagic may cause binwalk to fail to function properly. 
3. Conversely, updating libmagic to a version that works with binwalk may cause other utilities that rely on libmagic to fail. 

Currently, the following libmagic versions are known to work properly with binwalk (other versions may or may not work):

    5.18
    5.19
    5.20


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

Or, simply copy the `src/scripts/binida.py` file into IDA's `plugins` directory.


Uninstallation
==============

The following command will remove binwalk from your system. Note that this will *not* remove manually installed packages or tools:

```bash
$ sudo make uninstall
```

