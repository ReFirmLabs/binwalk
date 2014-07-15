FILE_VERSION=5.18
SSDEEP_VERSION=2.10
LIB_DIR="../binwalk/libs/"

.PHONY: all clean_libs clean distclean

all:
	make -C miniz
	cp miniz/*.so $(LIB_DIR)
	make -C compress
	cp compress/*.so $(LIB_DIR)
	if [ "$(BUILD_FUZZY)" -eq "1" ]; then make -C ssdeep-$(SSDEEP_VERSION) libfuzzy.la; fi
	if [ "$(BUILD_FUZZY)" -eq "1" ]; then cp ssdeep-$(SSDEEP_VERSION)/.libs/libfuzzy.so $(LIB_DIR); fi
	if [ "$(BUILD_MAGIC)" -eq "1" ]; then make -C file-$(FILE_VERSION)/src magic.h; fi # This must be done first for OSX, else MAGIC_VERSION is undefined
	if [ "$(BUILD_MAGIC)" -eq "1" ]; then make -C file-$(FILE_VERSION)/src libmagic.la; fi
	if [ "$(BUILD_MAGIC)" -eq "1" ]; then cp file-$(FILE_VERSION)/src/.libs/libmagic.so $(LIB_DIR); fi

clean_libs:
	rm -f $(LIB_DIR)*.so

clean: clean_libs
	make -C miniz clean
	make -C compress clean
	if [ "$(BUILD_FUZZY)" -eq "1" ]; then make -C ssdeep-$(SSDEEP_VERSION) clean; fi
	if [ "$(BUILD_MAGIC)" -eq "1" ]; then make -C file-$(FILE_VERSION) clean; fi

distclean: clean_libs
	make -C miniz distclean
	make -C compress distclean
	if [ "$(BUILD_FUZZY)" -eq "1" ]; then rm -rf `ls ./ssdeep-*.tar.gz | sed -e 's/\.tar\.gz//'`; fi
	if [ "$(BUILD_MAGIC)" -eq "1" ]; then rm -rf `ls ./file-*.tar.gz | sed -e 's/\.tar\.gz//'`; fi

