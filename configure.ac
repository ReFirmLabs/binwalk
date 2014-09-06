AC_PREREQ([2.65])
AC_INIT()

AC_PROG_CC
AC_LANG(C)

AC_TYPE_SIZE_T
AC_FUNC_MALLOC

AC_ARG_WITH([ida],
            [AS_HELP_STRING([--with-ida=$HOME/ida], [define the IDA install path])],
            [IDA_DIR=$withval],
            [IDA_DIR=$HOME/ida])

AC_ARG_WITH([python],
            [AS_HELP_STRING([--with-python=python], [explicitly install using the specified python interpreter (python2, python3, etc)])],
            [PYTHON=$withval],
            [PYTHON=python])

AC_ARG_ENABLE([clibs],
              [AS_HELP_STRING([--disable-clibs], [do not build/install binwalk c libraries])],,
              [BUILD_C_LIBS=yes])

AC_ARG_ENABLE([bundles],
              [AS_HELP_STRING([--disable-bundles], [do not build/install any bundled software])],,
              [BUILD_BUNDLES=yes])

AC_ARG_ENABLE([libmagic],
              [AS_HELP_STRING([--disable-libmagic], [do not build/install the bundled libmagic library])],,
              [BUILD_MAGIC=yes])

CFLAGS="-Wall -fPIC $CFLAGS"
INSTALL_OPTIONS="-m644"

if test "$prefix" != "NONE"
then
    echo "install prefix: $prefix"
fi

if test "$(uname)" == "Darwin"
then
	SONAME="-install_name"
	SOEXT="dylib"
else
	SONAME="-soname"
	SOEXT="so"
fi

if test "$BUILD_BUNDLES" == "no"
then
    BUILD_MAGIC=no
fi

if test "$BUILD_MAGIC" != "no"
then
    rm -rf $(ls ./src/bundles/file-*.tar.gz | sed -e 's/\.tar\.gz//')
    (cd ./src/bundles && tar -zxvf file-*.tar.gz > /dev/null)
    (cd ./src/bundles/file-*/ && ./configure) || exit 1
fi

AC_SUBST(BUILD_C_LIBS, $BUILD_C_LIBS)
AC_SUBST(BUILD_BUNDLES, $BUILD_BUNDLES)
AC_SUBST(BUILD_MAGIC, $BUILD_MAGIC)
AC_SUBST(PYTHON, $PYTHON)
AC_SUBST(IDA_DIR, $IDA_DIR)
AC_SUBST(SONAME, $SONAME)
AC_SUBST(SOEXT, $SOEXT)
AC_SUBST(PLATFORM, $(uname -s))
AC_SUBST(INSTALL_OPTIONS, $INSTALL_OPTIONS)
AC_CONFIG_FILES([Makefile])
AC_OUTPUT
