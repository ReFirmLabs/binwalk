#!/bin/bash

# Check for the --yes command line argument to skip yes/no prompts
if [ "$1" = "--yes" ]
then
    YES=1
else
    YES=0
fi

set -eu
set -o nounset
set -x

if ! which lsb_release > /dev/null
then
    function lsb_release {
        if [ -f /etc/os-release ]
        then
            [[ "$1" = "-i" ]] && cat /etc/os-release | grep ^"ID" | cut -d= -f 2
            [[ "$1" = "-r" ]] && cat /etc/os-release | grep "VERSION_ID" | cut -d= -d'"' -f 2
        elif [ -f /etc/lsb-release ]
        then
            [[ "$1" = "-i" ]] && cat /etc/lsb-release | grep "DISTRIB_ID" | cut -d= -f 2
            [[ "$1" = "-r" ]] && cat /etc/lsb-release | grep "DISTRIB_RELEASE" | cut -d= -f 2
        else
            echo Unknown
        fi
    }
fi

if [ $YES -eq 0 ]
then
    distro="${1:-$(lsb_release -i|cut -f 2)}"
    distro_version="${1:-$(lsb_release -r|cut -f 2|cut -c1-2)}"
else
    distro="${2:-$(lsb_release -i|cut -f 2)}"
    distro_version="${2:-$(lsb_release -r|cut -f 2|cut -c1-2)}"
fi
REQUIRED_UTILS="wget tar python"
APTCMD="apt"
APTGETCMD="apt-get"
YUMCMD="yum"
if [ $distro = "Kali" ]
then
    APT_CANDIDATES="git locales build-essential qt5base-dev mtd-utils gzip bzip2 tar arj lhasa p7zip p7zip-full cabextract util-linux firmware-mod-kit cramfsswap squashfs-tools zlib1g-dev liblzma-dev liblzo2-dev sleuthkit default-jdk lzop cpio"
elif [ $distro_version = "14" ]
then
    APT_CANDIDATES="git locales build-essential libqt4-opengl mtd-utils gzip bzip2 tar arj lhasa p7zip p7zip-full cabextract cramfsprogs cramfsswap squashfs-tools zlib1g-dev liblzma-dev liblzo2-dev sleuthkit default-jdk lzop srecord cpio"
elif [ $distro_version = "15" ]
then
    APT_CANDIDATES="git locales build-essential libqt4-opengl mtd-utils gzip bzip2 tar arj lhasa p7zip p7zip-full cabextract cramfsprogs cramfsswap squashfs-tools zlib1g-dev liblzma-dev liblzo2-dev sleuthkit default-jdk lzop srecord cpio"
elif [ $distro_version = "16" ]
then
    APT_CANDIDATES="git locales build-essential libqt4-opengl mtd-utils gzip bzip2 tar arj lhasa p7zip p7zip-full cabextract cramfsprogs cramfsswap squashfs-tools zlib1g-dev liblzma-dev liblzo2-dev sleuthkit default-jdk lzop srecord cpio"
elif [ $distro_version = "18" ]
then
    APT_CANDIDATES="git locales build-essential libqt4-opengl mtd-utils gzip bzip2 tar arj lhasa p7zip p7zip-full cabextract cramfsswap squashfs-tools zlib1g-dev liblzma-dev liblzo2-dev sleuthkit default-jdk lzop srecord cpio"
else
    APT_CANDIDATES="git locales build-essential qtbase5-dev mtd-utils gzip bzip2 tar arj lhasa p7zip p7zip-full cabextract cramfsswap squashfs-tools zlib1g-dev liblzma-dev liblzo2-dev sleuthkit default-jdk lzop srecord cpio"
fi
PYTHON3_APT_CANDIDATES=""
PYTHON3_YUM_CANDIDATES=""
YUM_CANDIDATES="git gcc gcc-c++ make openssl-devel qtwebkit-devel qt-devel gzip bzip2 tar arj p7zip p7zip-plugins cabextract squashfs-tools zlib zlib-devel lzo lzo-devel xz xz-compat-libs xz-libs xz-devel xz-lzma-compat python-backports-lzma lzip pyliblzma perl-Compress-Raw-Lzma lzop srecord"
PYTHON="$(which python3)"

# Check for root privileges
if [ $UID -eq 0 ]
then
    echo "UID is 0, sudo not required"
    SUDO=""
else
    SUDO="sudo -E"
    REQUIRED_UTILS="sudo $REQUIRED_UTILS"
fi

function install_yaffshiv
{
    git clone --quiet --depth 1 --branch "master" https://github.com/devttys0/yaffshiv
    (cd yaffshiv && $SUDO $PYTHON setup.py install)
    $SUDO rm -rf yaffshiv
}

function install_sasquatch
{
    git clone --quiet --depth 1 --branch "master" https://github.com/devttys0/sasquatch
    (cd sasquatch && $SUDO ./build.sh)
    $SUDO rm -rf sasquatch
}

function install_jefferson
{
    git clone --quiet --depth 1 --branch "master" https://github.com/sviehb/jefferson
    (cd jefferson && $SUDO $PYTHON -mpip install -r requirements.txt && $SUDO $PYTHON setup.py install)
    $SUDO rm -rf jefferson
}

function install_cramfstools
{
  # Downloads cramfs tools from sourceforge and installs them to $INSTALL_LOCATION
  TIME=`date +%s`
  INSTALL_LOCATION=/usr/local/bin

  # https://github.com/torvalds/linux/blob/master/fs/cramfs/README#L106
  git clone --quiet --depth 1 --branch "master" https://github.com/npitre/cramfs-tools
  # There is no "make install"
  (cd cramfs-tools \
  && make \
  && $SUDO install mkcramfs $INSTALL_LOCATION \
  && $SUDO install cramfsck $INSTALL_LOCATION)

  rm -rf cramfs-tools
}


function install_ubireader
{
    git clone --quiet --depth 1 --branch "master" https://github.com/jrspruitt/ubi_reader
    (cd ubi_reader && $SUDO $PYTHON setup.py install)
    $SUDO rm -rf ubi_reader
}

function install_pip_package
{
    PACKAGE="$1"
    $SUDO $PYTHON -mpip install $PACKAGE
}

function find_path
{
    FILE_NAME="$1"

    echo -ne "checking for $FILE_NAME..."
    which $FILE_NAME > /dev/null
    if [ $? -eq 0 ]
    then
        echo "yes"
        return 0
    else
        echo "no"
        return 1
    fi
}

# Make sure the user really wants to do this
if [ $YES -eq 0 ]
then
    echo ""
    echo "WARNING: This script will download and install all required and optional dependencies for binwalk."
    echo "         This script has only been tested on, and is only intended for, Debian based systems."
    echo "         Some dependencies are downloaded via unsecure (HTTP) protocols."
    echo "         This script requires internet access."
    echo "         This script requires root privileges."
    echo ""
    if [ $distro != Unknown ]
    then
        echo "         $distro $distro_version detected"
    else
        echo "WARNING: Distro not detected, using package-manager defaults"
    fi
    echo ""
    echo -n "Continue [y/N]? "
    read YN
    if [ "$(echo "$YN" | grep -i -e 'y' -e 'yes')" == "" ]
    then
        echo "Quitting..."
        exit 1
    fi
elif [ $distro != Unknown ]
then
     echo "$distro $distro_version detected"
else
    echo "WARNING: Distro not detected, using package-manager defaults"
fi

# Check to make sure we have all the required utilities installed
NEEDED_UTILS=""
for UTIL in $REQUIRED_UTILS
do
    find_path $UTIL
    if [ $? -eq 1 ]
    then
        NEEDED_UTILS="$NEEDED_UTILS $UTIL"
    fi
done

# Check for supported package managers and set the PKG_* envars appropriately
find_path $APTCMD
if [ $? -eq 1 ]
then
    find_path $APTGETCMD
    if [ $? -eq 1 ]
    then
        find_path $YUMCMD
        if [ $? -eq 1 ]
        then
            NEEDED_UTILS="$NEEDED_UTILS $APTCMD/$APTGETCMD/$YUMCMD"
        else
            PKGCMD="$YUMCMD"
            PKGCMD_OPTS="-y install"
            PKG_CANDIDATES="$YUM_CANDIDATES"
            PKG_PYTHON3_CANDIDATES="$PYTHON3_YUM_CANDIDATES"
        fi
    else
        PKGCMD="$APTGETCMD"
        PKGCMD_OPTS="install -y"
        PKG_CANDIDATES="$APT_CANDIDATES"
        PKG_PYTHON3_CANDIDATES="$PYTHON3_APT_CANDIDATES"
    fi
else
    if "$APTCMD" install -s -y dpkg > /dev/null
    then
        PKGCMD="$APTCMD"
        PKGCMD_OPTS="install -y"
        PKG_CANDIDATES="$APT_CANDIDATES"
        PKG_PYTHON3_CANDIDATES="$PYTHON3_APT_CANDIDATES"
    else
        PKGCMD="$APTGETCMD"
        PKGCMD_OPTS="install -y"
        PKG_CANDIDATES="$APT_CANDIDATES"
        PKG_PYTHON3_CANDIDATES="$PYTHON3_APT_CANDIDATES"
    fi
fi

if [ "$NEEDED_UTILS" != "" ]
then
    echo "Please install the following required utilities: $NEEDED_UTILS"
    exit 1
fi

# Do the install(s)
cd /tmp
$SUDO $PKGCMD $PKGCMD_OPTS $PKG_CANDIDATES
if [ $? -ne 0 ]
    then
    echo "Package installation failed: $PKG_CANDIDATES"
    exit 1
fi
install_pip_package "setuptools matplotlib capstone pycryptodome gnupg tk"
install_sasquatch
install_yaffshiv
install_jefferson
install_ubireader

if [ $distro_version = "18" ]
then
install_cramfstools
fi
