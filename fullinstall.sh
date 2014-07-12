#!/bin/bash
# binwalk prerequisite installer.
# installs prereq libs in $PREFIX.

PREFIX=/opt/binwalk
QUICK_START_SCRIPT_PREFIX=/usr/local
SSDEEP=ssdeep-2.10
FILE=file-5.19

SUDO=$(which sudo)

printf "Attempting to install binwalk prerequisites to $PREFIX...\n\n"
pushd /tmp > /dev/null

# check for presence of $PREFIX and create if necessary.
if [ ! -e $PREFIX ]; then
    $SUDO mkdir -p $PREFIX
fi

if [ ! -e $PREFIX ]; then
    printf "Could not create $PREFIX"
    exit 1
fi

# download and install ssdeep into $PREFIX
printf "Installing $SSDEEP...\n"
wget -q -O- "http://sourceforge.net/projects/ssdeep/files/$SSDEEP/$SSDEEP.tar.gz/download" | tar -zx
if [ -e $SSDEEP ]; then
    cd $SSDEEP
    ./configure -q --prefix=$PREFIX > /dev/null
    make -s > /dev/null
    sudo make -s install > /dev/null
    cd - > /dev/null
    rm -rf $SSDEEP
fi

# download and install libmagic into $PREFIX
printf "Installing $FILE...\n"
wget -q -O- "ftp://ftp.astron.com//pub/file/$FILE.tar.gz" | tar -zx
if [ -e $FILE ]; then
    cd $FILE
    ./configure -q --prefix=$PREFIX
    make -s clean > /dev/null
    make -s > /dev/null
    sudo make -s install > /dev/null
    cd - > /dev/null
    rm -rf $FILE
fi
#printf "\n\n\n"
printf "file/libmagic and ssdeep/libfuzzy have been installed in $PREFIX.\n"
#printf "To complete the install in $PREFIX, please run the following commands:\n\n"
#printf "PATH=$PREFIX/bin:\$PATH CPPFLAGS=-I$PREFIX/include LDFLAGS=-L$PREFIX/lib ./configure\n"
#printf "PATH=$PREFIX/bin:\$PATH CPPFLAGS=-I$PREFIX/include LDFLAGS=-L$PREFIX/lib make install\n"

popd > /dev/null

# install binwalk itself into prefix
printf "Installing binwalk into $PREFIX...\n"
export PATH=$PREFIX/bin:$PATH
export CPPFLAGS=-I$PREFIX/include
export LDFLAGS=-L$PREFIX/lib
./configure --prefix=$PREFIX > /dev/null
 sudo -E bash -c 'make install' > /dev/null
sudo make clean > /dev/null

printf "Installing binwalk quick-start script in $QUICK_START_SCRIPT_PREFIX...\n"
if [ -e $QUICK_START_SCRIPT_PREFIX/bin/binwalk ]; then
    echo "binwalk already installed in $QUICK_START_SCRIPT_PREFIX/bin!"
    exit 1
fi

PYVERSION=`python --version 2>&1 | perl -pe 's/.*\ ([0-9]\.[0-9]).*/$1/g'`
sudo echo "#!/bin/bash" > $QUICK_START_SCRIPT_PREFIX/bin/binwalk
sudo echo "export PYTHONPATH=$PREFIX/lib/python$PYVERSION/site-packages" >> $QUICK_START_SCRIPT_PREFIX/bin/binwalk
sudo echo "$PREFIX/bin/binwalk \"\$@\"" >> $QUICK_START_SCRIPT_PREFIX/bin/binwalk
sudo chmod +x $QUICK_START_SCRIPT_PREFIX/bin/binwalk
