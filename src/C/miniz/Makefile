LIBNAME=libtinfl.$(SOEXT)

all: $(LIBNAME)

$(LIBNAME): tinfl.o
	$(CC) $(CFLAGS) $(CPPFLAGS) -shared -Wl,$(SONAME),$(LIBNAME) tinfl.o -o $(LIBNAME) $(LDFLAGS)
	chmod +x $(LIBNAME)

tinfl.o:
	$(CC) $(CFLAGS) $(CPPFLAGS) -c tinfl.c

install:
	mkdir -p $(DESTDIR)$(LIBDIR)
	install $(INSTALL_OPTIONS) $(LIBNAME) $(DESTDIR)$(LIBDIR)/$(LIBNAME)

uninstall:
	rm -rf $(DESTDIR)$(LIBDIR)/$(LIBNAME)

.PHONY: clean distclean

clean:
	rm -f *.o $(LIBNAME)

distclean: clean
