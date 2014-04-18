AC_PREREQ([2.65])
AC_INIT()

AC_PROG_CC
AC_LANG(C)

AC_TYPE_SIZE_T
AC_FUNC_MALLOC

CFLAGS="-Wall -fPIC $CFLAGS"

if test "$(uname)" == "Darwin"
then
	SONAME="-install_name"
	SOEXT="dylib"
	INSTALL_OPTIONS="-m644"
else
	SONAME="-soname"
	SOEXT="so"
	INSTALL_OPTIONS="-D -m644"
fi

cd ./src/C/file-*/ && ./configure || exit 1
cd -
cd ./src/C/ssdeep-*/ && ./configure || exit 1
cd -

AC_SUBST(SONAME, $SONAME)
AC_SUBST(SOEXT, $SOEXT)
AC_SUBST(INSTALL_OPTIONS, $INSTALL_OPTIONS)
AC_CONFIG_FILES([Makefile])
AC_OUTPUT
