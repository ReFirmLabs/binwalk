#!/bin/bash
# Install pip dependencies.
# Requires that pip3 is already installed.

pip3 install uefi_firmware
pip3 install jefferson
pip3 install ubi-reader
pip3 install --upgrade lz4 zstandard git+https://github.com/clubby789/python-lzo@b4e39df
pip3 install --upgrade git+https://github.com/marin-m/vmlinux-to-elf

