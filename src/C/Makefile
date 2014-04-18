FILE_VERSION="5.14"
SSDEEP_VERSION="2.10"

.PHONY: all install clean distclean uninstall file_src_configure file_make_prep ssdeep_src_configure ssdeep_make_prep

all: ssdeep_src_configure ssdeep_make_prep file_src_configure file_make_prep
	make -C miniz
	make -C compress
	make -C ssdeep-$(SSDEEP_VERSION) libfuzzybinwalk.la
	make -C file-$(FILE_VERSION)/src libmagicbinwalk.la

install:
	make -C miniz install
	make -C compress install
	make -C ssdeep-$(SSDEEP_VERSION) install-libLTLIBRARIES
	make -C file-$(FILE_VERSION)/src install-libLTLIBRARIES

clean:
	make -C miniz clean
	make -C compress clean
	make -C ssdeep-$(SSDEEP_VERSION) clean
	make -C file-$(FILE_VERSION) clean

distclean:
	make -C miniz distclean
	make -C compress distclean
	make -C ssdeep-$(SSDEEP_VERSION) distclean
	make -C file-$(FILE_VERSION) distclean

uninstall:
	make -C miniz uninstall
	make -C compress uninstall
	make -C ssdeep-$(SSDEEP_VERSION) uninstall-libLTLIBRARIES
	make -C file-$(FILE_VERSION)/src uninstall-libLTLIBRARIES

file_src_configure:
	if [ ! -e ./file-$(FILE_VERSION)/Makefile ]; then cd ./file-$(FILE_VERSION) && ./configure; fi

file_make_prep:
	sed -e s/libmagic/libmagicbinwalk/g < ./file-$(FILE_VERSION)/src/Makefile >./file-$(FILE_VERSION)/src/mktmp
	mv ./file-$(FILE_VERSION)/src/mktmp ./file-$(FILE_VERSION)/src/Makefile

ssdeep_src_configure:
	if [ ! -e ./file-ssdeep-2.10/Makefile ]; then cd ./ssdeep-2.10 && ./configure; fi

ssdeep_make_prep:
	sed -e s/libfuzzy/libfuzzybinwalk/g < ./ssdeep-$(SSDEEP_VERSION)/Makefile >./ssdeep-$(SSDEEP_VERSION)/mktmp
	mv ./ssdeep-$(SSDEEP_VERSION)/mktmp ./ssdeep-$(SSDEEP_VERSION)/Makefile

