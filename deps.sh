#!/bin/bash
# Easy installer script for installing binwalk extraction utilities on Debian/RedHat systems.

SUDO=$(which sudo)
SUMOUNT="$1 $2"

function fmk
{
	# Get and build the firmware mod kit
	if [ -e /opt/firmware-mod-kit ]
	then
		if [ ! -e /opt/firmware-mod-kit/.git ]
		then
			$SUDO rm -rf /opt/firmware-mod-kit/
		fi
	fi

	if [ ! -e /opt/firmware-mod-kit ]
	then
		$SUDO mkdir -p /opt/firmware-mod-kit
        $SUDO chown $USER /opt/firmware-mod-kit
		$SUDO chmod o+rwx /opt/firmware-mod-kit
	fi

	if [ ! -e /opt/firmware-mod-kit/.git ]
	then
		git clone http://code.google.com/p/firmware-mod-kit /opt/firmware-mod-kit/
	fi

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


function debian
{
    # First make sure the repos are up to date
    $SUDO apt-get update

	# The appropriate unrar package goes under different names in Debian vs Ubuntu
	$SUDO apt-get -y install unrar
	if [ "$?" != "0" ]
	then
		echo "WARNING: Failed to install 'unrar' package, trying 'unrar-free' instead..."
		$SUDO apt-get -y install unrar-free
	fi

	# Install binwalk/fmk pre-requisites and extraction tools
    # lha isn't in newer ubuntu repos, so install it separately in case it fails
    $SUDO apt-get -y install lha
	$SUDO apt-get -y install git build-essential libtool autoconf mtd-utils zlib1g-dev liblzma-dev ncompress gzip bzip2 tar arj p7zip p7zip-full openjdk-6-jdk
	$SUDO apt-get -y install python-opengl python-qt4 python-qt4-gl python-numpy python-scipy
	if [ "$(which python3)" != "" ]
	then
		$SUDO apt-get -y install python3-pyqt4 python3-numpy python3-scipy
	fi
}

function redhat
{
	$SUDO yum groupinstall -y "Development Tools"
	$SUDO yum install -y git libtool autoconf mtd-utils unrar zlib1g-dev liblzma-dev xz-devel compress gzip bzip2 tar arj lha p7zip p7zip-full openjdk-6-jdk
	$SUDO yum install -y libqt4-opengl python-opengl python-qt4 python-qt4-gl python-numpy python-scipy
	if [ "$(which python3)" != "" ]
	then
		$SUDO yum -y install python3-pyqt4 python3-numpy python3-scipy
	fi
}

if [ "$1" == "" ] || [ "$1" == "--sumount" ]
then
	PLATFORM=$(python -c 'import platform; print (platform.system().lower())')
	DISTRO=$(python -c 'import platform; print (platform.linux_distribution()[0].strip("\"").split()[0].lower())')
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
    elementary)
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

# Get and build the firmware mod kit
fmk

