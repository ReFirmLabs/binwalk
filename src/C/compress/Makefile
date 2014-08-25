LIBNAME=libcompress42.$(SOEXT)

all: $(LIBNAME)

$(LIBNAME): compress42.o
	$(CC) $(CFLAGS) $(CPPFLAGS) -shared -Wl,$(SONAME),$(LIBNAME) compress42.o -o $(LIBNAME) $(LDFLAGS)
	chmod +x $(LIBNAME)

compress42.o:
	$(CC) $(CFLAGS) $(CPPFLAGS) compress42.c -c

install:
	mkdir -p $(DESTDIR)$(LIBDIR)
	install $(INSTALL_OPTIONS) $(LIBNAME) $(DESTDIR)$(LIBDIR)/$(LIBNAME)

uninstall:
	rm -rf $(DESTDIR)$(LIBDIR)/$(LIBNAME)

.PHONY: clean distclean

clean:
	rm -f *.o $(LIBNAME)

distclean: clean
