FILE_VERSION="5.14"

.PHONY: all install clean distclean uninstall file_src_configure file_make_prep

all: file_src_configure file_make_prep
	make -C miniz
	make -C compress
	make -C file-$(FILE_VERSION)

install:
	make -C miniz install
	make -C compress install
	make -C file-$(FILE_VERSION)/src install-libLTLIBRARIES

clean:
	make -C miniz clean
	make -C compress clean
	make -C file-$(FILE_VERSION) clean

distclean:
	make -C miniz distclean
	make -C compress distclean
	make -C file-$(FILE_VERSION) distclean

uninstall:
	make -C miniz uninstall
	make -C compress uninstall
	make -C file-$(FILE_VERSION)/src uninstall-libLTLIBRARIES

file_src_configure:
	if [ ! -e ./file-$(FILE_VERSION)/Makefile ]; then cd ./file-$(FILE_VERSION) && ./configure; fi

file_make_prep:
	sed -e s/libmagic/libmagicbinwalk/g < ./file-$(FILE_VERSION)/src/Makefile >./file-$(FILE_VERSION)/src/mktmp
	mv ./file-$(FILE_VERSION)/src/mktmp ./file-$(FILE_VERSION)/src/Makefile

