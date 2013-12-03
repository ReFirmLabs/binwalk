#!/bin/bash
# Easy installer script for Debian/RedHat systems.

SUDO=$(which sudo)
SUMOUNT="$1 $2"

function fmk
{
	# Get and build the firmware mod kit
	$SUDO rm -rf /opt/firmware-mod-kit/
	$SUDO mkdir -p /opt/firmware-mod-kit
	$SUDO chmod a+rwx /opt/firmware-mod-kit
	git clone https://code.google.com/p/firmware-mod-kit /opt/firmware-mod-kit/

	cd /opt/firmware-mod-kit/src
	./configure && $SUDO make

	if [ "$(echo "$SUMOUNT" | grep -e '--sumount')" != "" ]
	then
	        # The following will allow you - and others - to mount/unmount file systems without root permissions.
	        # This may be problematic, especially on a multi-user system, so think about it first.
	        $SUDO chown root ./mountcp/mountsu
	        $SUDO chmod u+s ./mountcp/mountsu
	        $SUDO chmod o-w ./mountcp/mountsu

	        $SUDO chown root ./mountcp/umountsu
	        $SUDO chmod u+s ./mountcp/umountsu
	        $SUDO chmod o-w ./mountcp/umountsu

	        $SUDO chown root ./jffs2/sunjffs2
	        $SUDO chmod u+s ./jffs2/sunjffs2
	        $SUDO chmod o-w ./jffs2/sunjffs2
	fi

	cd -
}

function libmagic
{
	SITE="ftp://ftp.astron.com/pub/file/"
	VERSION="5.11"
	OUTFILE="file-$VERSION.tar.gz"
	URL="$SITE$OUTFILE"

	echo "Downloading '$URL'..."
	wget "$URL"

	if [ -e "$OUTFILE" ]
	then
		echo "Installing libmagic / python-magic..."
		tar -zxvf "$OUTFILE"
		cd "file-$VERSION" && ./configure && make && $SUDO make install && cd python && $SUDO python ./setup.py install && cd ../..
		$SUDO rm -rf "file-$VERSION" "$OUTFILE"
	else
		echo "ERROR: Failed to download '$URL'!"
		echo "libmagic not installed."
	fi
}

function pyqtgraph
{
	SITE="http://www.pyqtgraph.org/downloads/"
	VERSION="0.9.8"
	OUTFILE="pyqtgraph-$VERSION.tar.gz"
	URL="$SITE$OUTFILE"

	echo "Downloading '$URL'..."
	wget "$URL"

	if [ -e "$OUTFILE" ]
	then
		echo "Installing pyqtgraph..."
		tar -zxvf "$OUTFILE"
		cd "pyqtgraph-$VERSION" && $SUDO python ./setup.py install && cd ..
		$SUDO rm -rf "pyqtgraph-$VERSION"
	else
		echo "ERROR: Failed to download '$URL'!"
		echo "pyqtgraph not installed."
	fi
}

function debian
{
	# The appropriate unrar package goes under different names in Debian vs Ubuntu
	$SUDO apt-get -y install unrar
	if [ "$?" != "0" ]
	then
		echo "WARNING: Failed to install 'unrar' package, trying 'unrar-free' instead..."
		$SUDO apt-get -y install unrar-free
	fi

	# Install binwalk/fmk pre-requisites and extraction tools
	$SUDO apt-get -y install git build-essential mtd-utils zlib1g-dev liblzma-dev ncompress gzip bzip2 tar arj p7zip p7zip-full openjdk-6-jdk
	$SUDO apt-get -y install python-opengl python-qt4 python-qt4-gl python-numpy python-scipy
}

function redhat
{
	$SUDO yum groupinstall -y "Development Tools"
	$SUDO yum install -y git mtd-utils unrar zlib1g-dev liblzma-dev xz-devel compress gzip bzip2 tar arj p7zip p7zip-full openjdk-6-jdk
	$SUDO yum install -y python-opengl python-qt4 python-qt4-gl python-numpy python-scipy
}

if [ "$1" == "" ] || [ "$1" == "--sumount" ]
then
	PLATFORM=$(python -c 'import platform; print platform.system().lower()')
	DISTRO=$(python -c 'import platform; print platform.linux_distribution()[0].lower()')
else
	DISTRO="$1"
fi

if [ "$DISTRO" == "" ]
then
	DISTRO="$PLATFORM"
fi

echo "Detected $DISTRO $PLATFORM"

case $DISTRO in
	debian)
		debian
		;;
	ubuntu) 
		debian
		;;
	linuxmint)
		debian
		;;
	knoppix)
		debian
		;;
	aptosid)
		debian
		;;

	redhat)
		redhat
		;;
	rhel)
		redhat
		;;
	fedora)
		redhat
		;;
	centos)
		redhat
		;;
	*)
		echo ""
		echo "This system is not recognized by easy install! You may need to install dependent packages manually."
		echo ""
		echo "If your system is a derivative of Debian or RedHat, you can try manually specifying your system type on the command line:"
		echo ""
		echo -e "\t$0 [debian | redhat] [--sumount]"
		echo ""
		exit 1
esac

if [ "$(python -c 'import magic; print (magic.MAGIC_NO_CHECK_TEXT)' 2>/dev/null)" == "" ]
then
	echo "python-magic not installed, or wrong version."
	libmagic
fi

if [ "$(python -c 'import pyqtgraph; print (pyqtgraph.__file__)' 2>/dev/null)" == "" ]
then
	echo "pyqtgraph not installed."
	pyqtgraph
fi

# Get and build the firmware mod kit
fmk

# Install binwalk
$SUDO python setup.py install

