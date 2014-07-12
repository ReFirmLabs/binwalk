AC_PREREQ([2.65])
AC_INIT()

AC_PROG_CC
AC_LANG(C)

AC_TYPE_SIZE_T
AC_FUNC_MALLOC

AC_ARG_WITH([python],
            [AS_HELP_STRING([--with-python=python], [explicitly install using the specified python interpreter (python2, python3, etc)])],
            [PYTHON=$withval],
            [PYTHON=python])

AC_ARG_ENABLE([clibs],
              [AS_HELP_STRING([--disable-clibs], [do not build/install dependent c libraries])],
              [BUILD_C_LIBS=0],
              [BUILD_C_LIBS=1])

CFLAGS="-Wall -fPIC $CFLAGS"

if test "$(uname)" == "Darwin"
then
	SONAME="-install_name"
	SOEXT="dylib"
	INSTALL_OPTIONS="-m644"
else
	SONAME="-soname"
	SOEXT="so"
	INSTALL_OPTIONS="-m644"
fi
dnl AS_IF([test "x$enable_foo" != "xno"], [

if test "$BUILD_C_LIBS" != "0"
then
    (cd ./src/C/file-*/ && autoreconf -v && ./configure) || exit 1
    (cd ./src/C/ssdeep-*/ && autoreconf -v && ./configure) || exit 1
fi

AC_SUBST(BUILD_C_LIBS, $BUILD_C_LIBS)
AC_SUBST(PYTHON, $PYTHON)
AC_SUBST(SONAME, $SONAME)
AC_SUBST(SOEXT, $SOEXT)
AC_SUBST(PLATFORM, $(uname -s))
AC_SUBST(INSTALL_OPTIONS, $INSTALL_OPTIONS)
AC_CONFIG_FILES([Makefile])
AC_OUTPUT
