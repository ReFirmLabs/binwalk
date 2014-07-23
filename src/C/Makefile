LIB_DIR="../$(PYLIBDIR)"

.PHONY: all clean_libs clean distclean

all:
	make -C miniz
	cp miniz/*.so $(LIB_DIR)
	make -C compress
	cp compress/*.so $(LIB_DIR)

clean_libs:
	rm -f $(LIB_DIR)/libtinfl.so
	rm -f $(LIB_DIR)/libcompress42.so

clean: clean_libs
	make -C miniz clean
	make -C compress clean

distclean: clean_libs
	make -C miniz distclean
	make -C compress distclean

