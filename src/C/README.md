About
-----

The libraries in this directory have been patched, extended, or otherwise modified from their original versions for use with binwalk.
Some may include third-party modifications not available in the standard library release.

Package mantainers should consult their particular distribution's rules regarding bundled libraries.

Installation
------------

These libraries will be built and installed by default, unless the `--disable-clibs` option is provided to the configure script.

The libraries will be installed to the `lib` sub-directory of the binwalk Python module so as to not conflict with existing libraries on the system.
