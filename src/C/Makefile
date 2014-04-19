FILE_VERSION="5.18"
SSDEEP_VERSION="2.10"

.PHONY: all install clean distclean uninstall file_make_prep ssdeep_make_prep

all: ssdeep_make_prep file_make_prep
	make -C miniz
	make -C compress
	make -C ssdeep-$(SSDEEP_VERSION) libinfuzzy.la
	make -C file-$(FILE_VERSION)/src magic.h # This must be done first for OSX, else MAGIC_VERSION is undefined
	make -C file-$(FILE_VERSION)/src libinmagic.la

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

file_make_prep:
	sed -e s/libmagic/libinmagic/g < ./file-$(FILE_VERSION)/src/Makefile >./file-$(FILE_VERSION)/src/mktmp
	mv ./file-$(FILE_VERSION)/src/mktmp ./file-$(FILE_VERSION)/src/Makefile

ssdeep_make_prep:
	sed -e s/libfuzzy/libinfuzzy/g < ./ssdeep-$(SSDEEP_VERSION)/Makefile >./ssdeep-$(SSDEEP_VERSION)/mktmp
	mv ./ssdeep-$(SSDEEP_VERSION)/mktmp ./ssdeep-$(SSDEEP_VERSION)/Makefile

