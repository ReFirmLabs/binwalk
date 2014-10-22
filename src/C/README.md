About
-----

The libraries in this directory have been patched, extended, or otherwise modified from their original versions for use with binwalk.

Specifically:

 o `libtinfl` includes several bug patches and wrapper functions not available in the upstream source.
 o `libcompress42` contains code taken from the ncompress Unix utility and turned into a library. To the author's knowledge, this functionality is not available elsewhere as a standard library.

Package mantainers should consult their particular distribution's rules on bundled code with regards to the above libraries.

Installation
------------

These libraries will be built and installed by default, unless the `--disable-clibs` option is provided to the configure script.

The libraries will be installed to the `lib` sub-directory of the binwalk Python module so as to not conflict with existing libraries on the system.
