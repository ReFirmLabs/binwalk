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
else
	SONAME="-soname"
fi

AC_SUBST(SONAME, $SONAME)
AC_CONFIG_FILES([Makefile])
AC_OUTPUT
