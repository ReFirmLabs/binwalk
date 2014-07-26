Before You Start
================

Binwalk supports Python 2.7 - 3.x. Although binwalk is slightly faster in Python 3, the Python OpenGL bindings are still experimental for Python 3, so Python 2.7 is recommended.

The following installation procedures assume that you are installing binwalk to be run using Python 2.7. If you want to use binwalk in Python 3, some package
names and installation procedures may differ slightly.

Installation
============

Installation follows the typical configure/make process (standard development tools such as gcc, make, and Python must be installed in order to build):

    $ ./configure
    $ make
    $ sudo make install

Binwalk's core features will work out of the box without any additional dependencies. However, to take advantage of binwalk's graphing and extraction capabilities, multiple supporting utilities/packages need to be installed.

To ease "dependency hell", a shell script named `deps.sh` is included which attempts to install all required dependencies for Debian and RedHat based systems:

    $ ./deps.sh

If you are running a different system, or prefer to install these dependencies manually, see the Dependencies section below.

Dependencies
============

The following dependencies are only required for optional binwalk features, such as file extraction and graphing capabilities. Unless otherwise specified, these dependencies are available from most Linux package managers.

Binwalk uses [pyqtgraph](http://www.pyqtgraph.org) to generate graphs and visualizations, which requires the following: 

    libqt4-opengl 
    python-opengl 
    python-qt4 
    python-qt4-gl 
    python-numpy 
    python-scipy

Binwalk relies on multiple external utilties in order to automatically extract/decompress files and data:

    mtd-utils
    zlib1g-dev
    liblzma-dev
    ncompress
    gzip
    bzip2
    tar
    arj
    p7zip
    cabextract
    p7zip-full
    openjdk-6-jdk
    firmware-mod-kit [https://code.google.com/p/firmware-mod-kit]

Bundled Software
================

For convenience, the following libraries are bundled with binwalk and will not conflict with system-wide libraries:

    libmagic
    libfuzzy
    pyqtgraph

Installation of any individual bundled library can be disabled at build time:

    $ ./configure --disable-libmagic --disable-libfuzzy --disable-pyqtgraph

Alternatively, installation of all bundled libraries can be disabled at build time:

    $ ./configure --disable-bundles

If a bundled library is disabled, the equivalent library must be installed to a standard system library location (e.g., `/usr/lib`, `/usr/local/lib`, etc) in order for binwalk to function properly.

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

    $ ./configure --with-python=python3


Uninstallation
==============

The following command will remove binwalk from your system. Note that this will *not* remove manually installed packages, or utilities installed via deps.sh:

    $ sudo make uninstall

