#!/bin/bash
# Easy installer script for Debian/RedHat/OSX systems.

function libmagic
{
	SITE="ftp://ftp.astron.com/pub/file/"
	# 5.11 is the most recent version that builds out of the box on OSX.
	VERSION="5.11"
	OUTFILE="file-$VERSION.tar.gz"
	URL="$SITE$OUTFILE"

	echo "Downloading '$URL'..."

	if [ "$(which wget)" != "" ]
	then
		wget "$URL"
	elif [ "$(which curl)" != "" ]
	then
		curl "$URL" > "$OUTFILE"
	fi

	if [ -e "$OUTFILE" ]
	then
		echo "Installing libmagic / python-magic..."
		tar -zxvf "$OUTFILE"
		cd "file-$VERSION" && ./configure && make && sudo make install && cd python && sudo python ./setup.py install && cd ../..
		sudo rm -rf "file-$VERSION" "$OUTFILE"
	else
		echo "ERROR: Failed to download '$URL'!"
		echo "libmagic not installed."
	fi
}

function debian
{
	# The appropriate unrar package goes under different names in Debian vs Ubuntu
	sudo apt-get -y install unrar-nonfree
	if [ "$?" != "0" ]
	then
		echo "WARNING: Failed to install 'unrar-nonfree' package, trying 'unrar' instead..."
		sudo apt-get -y install unrar
	fi

	# Install binwalk/fmk pre-requisites and extraction tools
	sudo apt-get -y install git build-essential mtd-utils zlib1g-dev liblzma-dev ncompress gzip bzip2 tar arj p7zip p7zip-full openjdk-6-jdk python-matplotlib
}

function redhat
{
	sudo yum groupinstall -y "Development Tools"
	sudo yum install -y git mtd-utils unrar zlib1g-dev liblzma-dev xz-devel compress gzip bzip2 tar arj p7zip p7zip-full openjdk-6-jdk python-matplotlib
}

function darwin
{
	if [ "$(which easy_install)" == "" ]
	then
		curl https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py | sudo python
	fi

	if [ "$(which easy_install)" != "" ]
	then
		easy_install -m numpy
		easy_install -m matplotlib
	fi
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
	
	darwin)
		darwin
		;;
	*)
		echo ""
		echo "This system is not recognized by easy install! You may need to install dependent packages manually."
		echo ""
		echo "If your system is a derivative of Debian, RedHat, or OSX, you can try manually specifying your system type on the command line:"
		echo ""
		echo -e "\t$0 [debian | redhat | darwin] [--sumount]"
		echo ""
		exit 1
esac

if [ "$(python -c 'import magic; print (magic.MAGIC_NO_CHECK_TEXT)' 2>/dev/null)" == "" ]
then
	echo "python-magic not installed, or wrong version."
	libmagic
fi

# FMK doesn't support OSX.
if [ "$DISTRO" != "darwin" ]
then
	# Get and build the firmware mod kit
	sudo rm -rf /opt/firmware-mod-kit/
	sudo mkdir -p /opt/firmware-mod-kit
	sudo chmod a+rwx /opt/firmware-mod-kit
	git clone https://code.google.com/p/firmware-mod-kit /opt/firmware-mod-kit/

	cd /opt/firmware-mod-kit/src
	./configure && sudo make
	if [ "$1" == "--sumount" ] || [ "$2" == "--sumount" ]
	then
		# The following will allow you - and others - to mount/unmount file systems without root permissions.
		# This may be problematic, especially on a multi-user system, so think about it first.
		sudo chown root ./mountcp/mountsu
		sudo chmod u+s ./mountcp/mountsu
		sudo chmod o-w ./mountcp/mountsu

		sudo chown root ./mountcp/umountsu
		sudo chmod u+s ./mountcp/umountsu
		sudo chmod o-w ./mountcp/umountsu

		sudo chown root ./jffs2/sunjffs2
	        sudo chmod u+s ./jffs2/sunjffs2
	        sudo chmod o-w ./jffs2/sunjffs2
	fi
	cd -
fi

# Install binwalk
sudo python setup.py install

