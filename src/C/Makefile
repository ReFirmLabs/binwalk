FILE_VERSION=5.18
SSDEEP_VERSION=2.10

.PHONY: all install clean distclean uninstall file_make_prep ssdeep_make_prep

all: ssdeep_make_prep file_make_prep
	make -C miniz
	make -C compress
	if [ "$(BUILD_FUZZY)" -eq "1" ]; then make -C ssdeep-$(SSDEEP_VERSION) libinfuzzy.la; fi
	if [ "$(BUILD_MAGIC)" -eq "1" ]; then make -C file-$(FILE_VERSION)/src magic.h; fi # This must be done first for OSX, else MAGIC_VERSION is undefined
	if [ "$(BUILD_MAGIC)" -eq "1" ]; then make -C file-$(FILE_VERSION)/src libinmagic.la; fi

install:
	make -C miniz install
	make -C compress install
	if [ "$(BUILD_FUZZY)" -eq "1" ]; then make -C ssdeep-$(SSDEEP_VERSION) install-libLTLIBRARIES; fi
	if [ "$(BUILD_MAGIC)" -eq "1" ]; then make -C file-$(FILE_VERSION)/src install-libLTLIBRARIES; fi

clean:
	make -C miniz clean
	make -C compress clean
	if [ "$(BUILD_FUZZY)" -eq "1" ]; then make -C ssdeep-$(SSDEEP_VERSION) clean; fi
	if [ "$(BUILD_MAGIC)" -eq "1" ]; then make -C file-$(FILE_VERSION) clean; fi

distclean:
	make -C miniz distclean
	make -C compress distclean
	if [ "$(BUILD_FUZZY)" -eq "1" ]; then make -C ssdeep-$(SSDEEP_VERSION) distclean; fi
	if [ "$(BUILD_MAGIC)" -eq "1" ]; then make -C file-$(FILE_VERSION) distclean; fi

uninstall:
	make -C miniz uninstall
	make -C compress uninstall
	if [ "$(BUILD_FUZZY)" -eq "1" ]; then make -C ssdeep-$(SSDEEP_VERSION) uninstall-libLTLIBRARIES; fi
	if [ "$(BUILD_MAGIC)" -eq "1" ]; then make -C file-$(FILE_VERSION)/src uninstall-libLTLIBRARIES; fi

file_make_prep:
	if [ "$(BUILD_MAGIC)" -eq "1" ]; then sed -e s/libmagic/libinmagic/g < ./file-$(FILE_VERSION)/src/Makefile >./file-$(FILE_VERSION)/src/mktmp; fi
	if [ "$(BUILD_MAGIC)" -eq "1" ]; then mv -f ./file-$(FILE_VERSION)/src/mktmp ./file-$(FILE_VERSION)/src/Makefile; fi

ssdeep_make_prep:
	if [ "$(BUILD_FUZZY)" -eq "1" ]; then sed -e s/libfuzzy/libinfuzzy/g < ./ssdeep-$(SSDEEP_VERSION)/Makefile >./ssdeep-$(SSDEEP_VERSION)/mktmp; fi
	if [ "$(BUILD_FUZZY)" -eq "1" ]; then mv -f ./ssdeep-$(SSDEEP_VERSION)/mktmp ./ssdeep-$(SSDEEP_VERSION)/Makefile; fi

