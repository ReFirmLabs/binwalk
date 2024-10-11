#!/bin/bash
# Install dependencies from source.
# Requires that git and build tools (make, gcc, etc) are already installed.

# Install dumpifs
cd /tmp
git clone https://github.com/askac/dumpifs.git
cd /tmp/dumpifs
make dumpifs
sudo cp ./dumpifs /usr/local/bin/dumpifs
cd /tmp
sudo rm -rf /tmp/dumpifs


# Install LZFSE utility and library
cd /tmp
git clone https://github.com/lzfse/lzfse.git
cd /tmp/lzfse
sudo make install
cd /tmp
sudo rm -rf /tmp/lzfse


# Install dmg2img with LZFSE support
cd /tmp
git clone https://github.com/Lekensteyn/dmg2img.git
cd /tmp/dmg2img
make dmg2img HAVE_LZFSE=1
sudo make install
cd /tmp
sudo rm -rf /tmp/dmg2img

# Install srec2bin
mkdir /tmp/srec
cd /tmp/srec
wget http://www.goffart.co.uk/s-record/download/srec_151_src.zip
unzip srec_151_src.zip
make
sudo cp srec2bin /usr/local/bin/
cd /tmp
sudo rm -rf /tmp/srec
