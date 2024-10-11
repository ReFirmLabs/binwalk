#!/bin/bash
# Install pip dependencies.
# Requires that pip3 is already installed.

sudo pip3 install uefi_firmware
sudo pip3 install jefferson
sudo pip3 install ubi-reader
sudo pip3 install --upgrade lz4 zstandard git+https://github.com/clubby789/python-lzo@b4e39df
sudo pip3 install --upgrade git+https://github.com/marin-m/vmlinux-to-elf

