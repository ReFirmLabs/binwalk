Description
===========

Binwalk is a fast, easy to use tool for analyzing, reverse engineering, and extracting firmware images.

Installation
============

Binwalk follows the standard Python installation procedure:

```bash
$ sudo python setup.py install
```

If you're running Python 2.x, you'll also want to install the Python lzma module:

```bash
$ sudo apt-get install python-lzma
```

For instructions on installing optional dependencies, see [INSTALL.md](https://github.com/devttys0/binwalk/blob/master/INSTALL.md).


Usage
=====

Basic usage is simple:

```bash
$ binwalk firmware.bin

DECIMAL       HEXADECIMAL     DESCRIPTION
--------------------------------------------------------------------------------
0             0x0             TRX firmware header, little endian, header size: 28 bytes, image size: 14766080 bytes, CRC32: 0x6980E553 flags: 0x0, version: 1
28            0x1C            LZMA compressed data, properties: 0x5D, dictionary size: 65536 bytes, uncompressed size: 5494368 bytes
2319004       0x23629C        Squashfs filesystem, little endian, version 4.0, compression: xz, size: 12442471 bytes, 3158 inodes, blocksize: 131072 bytes, blocksize: 131072 bytes, created: 2014-05-21 22:38:47
```

For additional examples and descriptions of advanced options, see the [wiki](https://github.com/devttys0/binwalk/wiki).
