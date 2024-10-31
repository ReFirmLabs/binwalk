#!/bin/bash

# Get the path to this script's directory, regardless of where it is run from
SCRIPT_DIRECTORY=$(dirname -- "$( readlink -f -- "$0"; )")

# Install dependencies from apt repository
DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get -y install \
    p7zip-full \
    zstd \
    tar \
    unzip \
    sleuthkit \
    cabextract \
    curl \
    wget \
    git \
    lz4 \
    lzop \
    device-tree-compiler \
    unrar \
    unyaffs \
    python3-pip \
    build-essential \
    clang \
    liblzo2-dev \
    libucl-dev \
    liblz4-dev \
    libbz2-dev \
    zlib1g-dev \
    libfontconfig1-dev \
    liblzma-dev \
    libssl-dev

# Install sasquatch Debian package
curl -L -o sasquatch_1.0.deb "https://github.com/onekey-sec/sasquatch/releases/download/sasquatch-v4.5.1-4/sasquatch_1.0_$(dpkg --print-architecture).deb"
dpkg -i sasquatch_1.0.deb
rm sasquatch_1.0.deb

# Install Python dependencies
source ${SCRIPT_DIRECTORY}/pip.sh

# Install dependencies from source
source ${SCRIPT_DIRECTORY}/src.sh
