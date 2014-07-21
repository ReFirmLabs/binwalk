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

Binwalk uses [pyqtgraph](http://www.pyqtgraph.org) to generate graphs and visualizations; pyqtgraph requires the following Python modules: 

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
    [firmware-mod-kit](https://code.google.com/p/firmware-mod-kit)


Uninstallation
==============

The following command will remove binwalk from your system. Note that this will *not* remove manually installed packages, or utilities installed via deps.sh:

    $ sudo make uninstall

