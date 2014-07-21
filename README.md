Binwalk
=======

Binwalk is a fast, easy to use tool for analyzing, reverse engineering, and extracting firmware images.

See [binwalk.org](http://binwalk.org) for usage, screenshots and examples.

Installation
============

Binwalk follows the standard Unix configure/make installation procedure:

    $ ./configure
    $ make
    $ sudo make install

For convenience, optional dependancies for automatic extraction and graphical visualizations can be installed by running the included `deps.sh` script:

    $ ./deps.sh

If your system is not supported by deps.sh, or if you wish to manually install dependancies, see INSTALL.md.

For advanced installation options, see INSTALL.md.

Usage
=====

Basic usage is simple:

    $ binwalk firmware.bin

For additional examples and desriptions of advanced options, see the [wiki](http://binwalk.org/binwiki/).
