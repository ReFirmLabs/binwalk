LIBNAME=libtinfl.$(SOEXT)

all: $(LIBNAME)

$(LIBNAME): tinfl_wrapper.o
	$(CC) $(CFLAGS) $(CPPFLAGS) -shared -Wl,$(SONAME),$(LIBNAME) tinfl_wrapper.o -o $(LIBNAME) $(LDFLAGS)
	chmod +x $(LIBNAME)

tinfl_wrapper.o:
	$(CC) $(CFLAGS) $(CPPFLAGS) -c tinfl_wrapper.c

install:
	mkdir -p $(DESTDIR)$(LIBDIR)
	install $(INSTALL_OPTIONS) $(LIBNAME) $(DESTDIR)$(LIBDIR)/$(LIBNAME)

uninstall:
	rm -rf $(DESTDIR)$(LIBDIR)/$(LIBNAME)

.PHONY: clean distclean

clean:
	rm -f *.o $(LIBNAME)

distclean: clean
