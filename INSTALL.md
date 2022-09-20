Before You Start
================

Binwalk supports Python 3.6+. 

Installation
============

Installation follows the typical Python installation procedure:

```bash
# Python3.x
$ sudo python3 setup.py install
```

**NOTE**: Older versions of binwalk (e.g., v1.0) are not compatible with the latest version of binwalk. It is strongly recommended that you uninstall any existing binwalk installations before installing the latest version in order to avoid API conflicts.

Dependencies
============

Besides a Python interpreter, there are no installation dependencies for binwalk. All dependencies are optional run-time dependencies, and unless otherwise specified, are available from most Linux package managers.

Binwalk uses the `nosetest` library for tests and `coverage` for test-coverage:

```bash
$ sudo pip install nose coverage
```

Binwalk uses the `pycryptodome` (`pycrypto`-compatible module that is still maintained) library to decrypt some known encrypted firmware images:

```bash
$ sudo pip install pycryptodome
```

Binwalk uses [pyqtgraph](http://www.pyqtgraph.org) to generate graphs and visualizations, which requires the following (exact dependencies may vary based on your distro refer to `deps.sh` for more details): 

```bash
$ sudo apt-get install libqt4-opengl python3-opengl python3-pyqt4 python3-pyqt4.qtopengl python3-numpy python3-scipy python3-pip
$ sudo pip3 install pyqtgraph
```

Binwalk's `--disasm` option requires the [Capstone](http://www.capstone-engine.org/) disassembly framework and its corresponding Python bindings:

```bash
$ sudo pip install capstone
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
# Python3
$ sudo python3 setup.py uninstall
```

Note that this does _not_ remove any of the manually installed dependencies.

