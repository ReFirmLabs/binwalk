# Binwalk

[![Build Status](https://travis-ci.org/ReFirmLabs/binwalk.svg?branch=master)](https://travis-ci.org/ReFirmLabs/binwalk)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/ReFirmLabs/binwalk/graphs/commit-activity)
[![GitHub license](https://img.shields.io/github/license/ReFirmLabs/binwalk.svg)](https://github.com/ReFirmLabs/binwalk/blob/master/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/badges/shields.svg?style=social&label=Stars)](https://github.com/ReFirmLabs/binwalk/stargazers)

Binwalk is a fast, easy to use tool for analyzing, reverse engineering, and extracting firmware images.


### Installation and Usage

* [Installation](./INSTALL.md)
* [API](./API.md)
* [Supported Platforms](https://github.com/ReFirmLabs/binwalk/wiki/Supported-Platforms)
* [Getting Started](https://github.com/ReFirmLabs/binwalk/wiki/Quick-Start-Guide)
* [Binwalk Command Line Usage](https://github.com/ReFirmLabs/binwalk/wiki/Usage)
* [Binwalk IDA Plugin Usage](https://github.com/ReFirmLabs/binwalk/wiki/Creating-Custom-Plugins)

More information on [Wiki](https://github.com/ReFirmLabs/binwalk/wiki)

## Quick start

### Installation
Binwalk follows the standard Python installation procedure:

```bash
$ sudo python setup.py install
```

If you're running Python 2.x, installing the optional Python lzma module is strongly recommended (but not required):

```bash
$ sudo apt-get install python-lzma
```

For instructions on installing other optional dependencies, see [installation guide](https://github.com/ReFirmLabs/binwalk/blob/master/INSTALL.md).


### Usage

Basic usage is simple:

```bash
$ binwalk firmware.bin

DECIMAL       HEXADECIMAL     DESCRIPTION
--------------------------------------------------------------------------------
0             0x0             TRX firmware header, little endian, header size: 28 bytes, image size: 14766080 bytes, CRC32: 0x6980E553 flags: 0x0, version: 1
28            0x1C            LZMA compressed data, properties: 0x5D, dictionary size: 65536 bytes, uncompressed size: 5494368 bytes
2319004       0x23629C        Squashfs filesystem, little endian, version 4.0, compression: xz, size: 12442471 bytes, 3158 inodes, blocksize: 131072 bytes, blocksize: 131072 bytes, created: 2014-05-21 22:38:47
```

For additional examples and descriptions of advanced options, see the [wiki](https://github.com/ReFirmLabs/binwalk/wiki).
