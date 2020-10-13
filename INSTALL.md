Before You Start
================

Binwalk supports Python 2.7 - 3.x. Although most systems have Python2.7 set as their default Python interpreter, binwalk does run faster in Python3. Installation procedures for both are provided below.

Installation
============

Installation follows the typical Python installation procedure:

```bash
# Python2.7
$ sudo python setup.py install
```

```bash
# Python3.x
$ sudo python3 setup.py install
```

**NOTE**: Older versions of binwalk (e.g., v1.0) are not compatible with the latest version of binwalk. It is strongly recommended that you uninstall any existing binwalk installations before installing the latest version in order to avoid API conflicts.

Dependencies
============

Besides a Python interpreter, there are no installation dependencies for binwalk. All dependencies are optional run-time dependencies, and unless otherwise specified, are available from most Linux package managers.

Although all binwalk run-time dependencies are optional, the `python-lzma` module is highly recommended for improving the reliability of signature scans. This module is included by default in Python3, but must be installed separately for Python2.7:

```bash
$ sudo apt-get install python-lzma
```

Binwalk uses the `nosetest` library for tests and `coverage` for test-coverage:

```bash
$ sudo pip install nose coverage
```

Binwalk uses the `pycrypto` library to decrypt some known encrypted firmware images:

```bash
# Python2.7
$ sudo apt-get install python-crypto
```

```bash
# Python3.x
$ sudo apt-get install python3-crypto
```

Binwalk uses [pyqtgraph](http://www.pyqtgraph.org) to generate graphs and visualizations, which requires the following: 

```bash
# Python2.7
$ sudo apt-get install libqt4-opengl python-opengl python-qt4 python-qt4-gl python-numpy python-scipy python-pip
$ sudo pip install pyqtgraph
```

```bash
# Python3.x
$ sudo apt-get install libqt4-opengl python3-opengl python3-pyqt4 python3-pyqt4.qtopengl python3-numpy python3-scipy python3-pip
$ sudo pip3 install pyqtgraph
```

Binwalk's `--disasm` option requires the [Capstone](http://www.capstone-engine.org/) disassembly framework and its corresponding Python bindings:

```bash
# Python2.7
$ sudo apt-get install python-pip
$ sudo pip install capstone
```

```bash
# Python3.x
$ sudo apt-get install python3-pip
$ sudo pip3 install capstone
```

Binwalk relies on multiple external utilties in order to automatically extract/decompress files and data:

```bash
# Install standard extraction utilities
$ sudo apt-get install mtd-utils gzip bzip2 tar arj lhasa p7zip p7zip-full cabextract cramfsprogs cramfsswap squashfs-tools sleuthkit default-jdk lzop srecord
```

```bash
# Install sasquatch to extract non-standard SquashFS images
$ sudo apt-get install zlib1g-dev liblzma-dev liblzo2-dev
$ git clone https://github.com/devttys0/sasquatch
$ (cd sasquatch && ./build.sh)
```

```bash
# Install jefferson to extract JFFS2 file systems
$ sudo pip install cstruct
$ git clone https://github.com/sviehb/jefferson
$ (cd jefferson && sudo python setup.py install)
```

```bash
# Install ubi_reader to extract UBIFS file systems
$ sudo apt-get install liblzo2-dev python-lzo
$ git clone https://github.com/jrspruitt/ubi_reader
$ (cd ubi_reader && sudo python setup.py install)
```

```bash
# Install yaffshiv to extract YAFFS file systems
$ git clone https://github.com/devttys0/yaffshiv
$ (cd yaffshiv && sudo python setup.py install)
```

```bash
# Install unstuff (closed source) to extract StuffIt archive files
$ wget -O - http://downloads.tuxfamily.org/sdtraces/stuffit520.611linux-i386.tar.gz | tar -zxv
$ sudo cp bin/unstuff /usr/local/bin/
```

Note that for Debian/Ubuntu users, all of the above dependencies can be installed automatically using the included `deps.sh` script:

```bash
$ sudo ./deps.sh
```

Installing the IDA Plugin
=========================

If IDA is installed on your system, you may optionally install the binwalk IDA plugin:

```bash
$ python setup.py idainstall --idadir=/home/user/ida
```

Likewise, the binwalk IDA plugin can be uninstalled:

```bash
$ python setup.py idauninstall --idadir=/home/user/ida
```


Uninstalling Binwalk
====================

If binwalk has been installed to a standard system location (e.g., via `setup.py install`), it can be removed by running:

```bash
# Python2.7
$ sudo python setup.py uninstall
```

```bash
# Python3
$ sudo python3 setup.py uninstall
```

Note that this does _not_ remove any of the manually installed dependencies.

