LIBNAME=libcompress42.so

all: clean $(LIBNAME)

$(LIBNAME): compress42.o
	$(CC) $(CFLAGS) -shared -Wl,$(SONAME),$(LIBNAME) compress42.o -o $(LIBNAME) $(LDFLAGS)

compress42.o:
	$(CC) $(CFLAGS) compress42.c -c

install:
	install $(INSTALL_OPTIONS) $(LIBNAME) $(DESTDIR)$(LIBDIR)/$(LIBNAME)

.PHONY: clean distclean

clean:
	rm -f *.o

distclean: clean
	rm -f $(LIBNAME)
