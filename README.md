Description
===========

Binwalk is a fast, easy to use tool for analyzing, reverse engineering, and extracting firmware images.

Installation
============

Binwalk follows the standard Unix configure/make installation procedure:

```bash
$ autoreconf
$ ./configure
$ make
$ sudo make install
```

If you're running Python 2.x, you'll also want to install the Python lzma module:

```bash
$ sudo apt-get install python-lzma
```

For instructions on installing optional dependencies, see `INSTALL.md`.

For advanced installation options, see `INSTALL.md`.

Usage
=====

Basic usage is simple:

```bash
$ binwalk firmware.bin
```

For additional examples and descriptions of advanced options, see the [wiki](https://github.com/devttys0/binwalk/wiki).
