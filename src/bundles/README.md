About
-----

The libraries contained in this directory are provided for convenience of installation, and have not been modified.

Package maintainers can generally replace these libraries with standard libraries from their particular distribution's package repository, however, the root `INSTALL.md` file should be consulted first.

Installation
------------

These libraries are not built or installed by default, unless the `--enable-<libname>` option is provided to the configure script.

They will be installed into the `libs` sub-directory of the binwalk Python module, so as to not conflict with existing libraries on the system.
