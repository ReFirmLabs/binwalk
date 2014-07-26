LIB_DIR="../$(PYLIBDIR)"

.PHONY: all clean_libs clean distclean

all:
	make -C miniz
	cp miniz/*.$(SOEXT) $(LIB_DIR)
	make -C compress
	cp compress/*.$(SOEXT) $(LIB_DIR)

clean_libs:
	rm -f $(LIB_DIR)/libtinfl.$(SOEXT)
	rm -f $(LIB_DIR)/libcompress42.$(SOEXT)

clean: clean_libs
	make -C miniz clean
	make -C compress clean

distclean: clean_libs
	make -C miniz distclean
	make -C compress distclean

