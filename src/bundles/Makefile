LIB_DIR="../$(PYLIBDIR)"
FILE_VERSION=`ls file-*.tar.gz | cut -d'-' -f2 | cut -d '.' -f1,2`

.PHONY: all clean_libs clean distclean

all:
	if [ "$(BUILD_MAGIC)" = "yes" ]; then make -C file-$(FILE_VERSION)/src magic.h; fi # This must be done first for OSX, else MAGIC_VERSION is undefined
	if [ "$(BUILD_MAGIC)" = "yes" ]; then make -C file-$(FILE_VERSION)/src libmagic.la; fi
	if [ "$(BUILD_MAGIC)" = "yes" ]; then cp file-$(FILE_VERSION)/src/.libs/libmagic.$(SOEXT) $(LIB_DIR); fi

clean_libs:
	rm -f $(LIB_DIR)/libmagic.$(SOEXT)

clean: clean_libs
	if [ "$(BUILD_MAGIC)" = "yes" ]; then make -C file-$(FILE_VERSION) clean; fi

distclean: clean_libs
	rm -rf ./file-$(FILE_VERSION)

