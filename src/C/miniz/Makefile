LIBNAME=libtinfl.$(SOEXT)

all: clean $(LIBNAME)

$(LIBNAME): tinfl.o
	$(CC) $(CFLAGS) -shared -Wl,$(SONAME),$(LIBNAME) tinfl.o -o $(LIBNAME) $(LDFLAGS)

tinfl.o:
	$(CC) $(CFLAGS) -c tinfl.c

install:
	install $(INSTALL_OPTIONS) $(LIBNAME) $(DESTDIR)$(LIBDIR)/$(LIBNAME)

.PHONY: clean distclean

clean:
	rm -f *.o

distclean: clean
	rm -f $(LIBNAME)
