#!/bin/bash
# Install pip dependencies.
# Requires that pip3 is already installed.

PIP_OPTIONS='--break-system-packages'

pip3 install uefi_firmware $PIP_OPTIONS
pip3 install jefferson $PIP_OPTIONS
pip3 install ubi-reader $PIP_OPTIONS
pip3 install --upgrade lz4 zstandard git+https://github.com/clubby789/python-lzo@b4e39df $PIP_OPTIONS
pip3 install --upgrade git+https://github.com/marin-m/vmlinux-to-elf $PIP_OPTIONS

