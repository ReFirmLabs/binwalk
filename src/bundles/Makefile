LIB_DIR="../$(PYLIBDIR)"
FILE_VERSION=`ls file-*.tar.gz | cut -d'-' -f2 | cut -d '.' -f1,2`
SSDEEP_VERSION=`ls ssdeep-*.tar.gz | cut -d'-' -f2 | cut -d '.' -f1,2`
PYQTGRAPH_VERSION=`ls pyqtgraph-*.tar.gz | cut -d'-' -f2 | cut -d '.' -f1,2,3`

.PHONY: all clean_libs clean distclean

all:
	if [ "$(BUILD_FUZZY)" -eq "1" ]; then make -C ssdeep-$(SSDEEP_VERSION) libfuzzy.la; fi
	if [ "$(BUILD_FUZZY)" -eq "1" ]; then cp ssdeep-$(SSDEEP_VERSION)/.libs/libfuzzy.$(SOEXT) $(LIB_DIR); fi
	if [ "$(BUILD_MAGIC)" -eq "1" ]; then make -C file-$(FILE_VERSION)/src magic.h; fi # This must be done first for OSX, else MAGIC_VERSION is undefined
	if [ "$(BUILD_MAGIC)" -eq "1" ]; then make -C file-$(FILE_VERSION)/src libmagic.la; fi
	if [ "$(BUILD_MAGIC)" -eq "1" ]; then cp file-$(FILE_VERSION)/src/.libs/libmagic.$(SOEXT) $(LIB_DIR); fi
	if [ "$(BUILD_PYQTGRAPH)" -eq "1" ]; then cp -R pyqtgraph-$(PYQTGRAPH_VERSION)/pyqtgraph $(LIB_DIR)/; fi

clean_libs:
	rm -f $(LIB_DIR)/libmagic.$(SOEXT)
	rm -f $(LIB_DIR)/libfuzzy.$(SOEXT)
	rm -rf $(LIB_DIR)/pyqtgraph

clean: clean_libs
	if [ "$(BUILD_FUZZY)" -eq "1" ]; then make -C ssdeep-$(SSDEEP_VERSION) clean; fi
	if [ "$(BUILD_MAGIC)" -eq "1" ]; then make -C file-$(FILE_VERSION) clean; fi

distclean: clean_libs
	rm -rf ./ssdeep-$(SSDEEP_VERSION)
	rm -rf ./file-$(FILE_VERSION)
	rm -rf ./pyqtgraph-$(PYQTGRAPH_VERSION)

