#!/bin/bash
# Install dependencies from source.
# Requires that git and build tools (make, gcc, etc) are already installed.

# Install dumpifs
cd /tmp
git clone https://github.com/askac/dumpifs.git
cd /tmp/dumpifs
make dumpifs
cp ./dumpifs /usr/local/bin/dumpifs
cd /tmp
rm -rf /tmp/dumpifs


# Install LZFSE utility and library
cd /tmp
git clone https://github.com/lzfse/lzfse.git
cd /tmp/lzfse
make install
cd /tmp
rm -rf /tmp/lzfse


# Install dmg2img with LZFSE support
cd /tmp
git clone https://github.com/Lekensteyn/dmg2img.git
cd /tmp/dmg2img
make dmg2img HAVE_LZFSE=1
make install
cd /tmp
rm -rf /tmp/dmg2img
