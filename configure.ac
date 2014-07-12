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
INSTALL_OPTIONS="-m644"

if test "$(uname)" == "Darwin"
then
	SONAME="-install_name"
	SOEXT="dylib"
else
	SONAME="-soname"
	SOEXT="so"
fi

AC_CHECK_PROG(SSDEEP_CHECK,ssdeep,yes)
if test x"$SSDEEP_CHECK" != x"yes" ; then
    AC_MSG_ERROR([Cannot find ssdeep/libfuzzy.])
fi
AC_CHECK_LIB([fuzzy],[fuzzy_hash_buf], [], AC_MSG_ERROR([Cannot find libfuzzy (part of ssdeep).]))

AC_MSG_CHECKING([checking ssdeep version...])
SSDEEP_VERSION=`ssdeep -V`
AC_MSG_RESULT([$SSDEEP_VERSION])
AS_VERSION_COMPARE([$SSDEEP_VERSION], [2.10], AC_MSG_ERROR([binwalk needs ssdeep/libfuzzy version 2.10 or higher.]), [], [])


AC_CHECK_LIB([magic],[magic_open], [], AC_MSG_ERROR([Cannot find libmagic.]))
AC_MSG_CHECKING([checking libmagic version...])
AC_COMPUTE_INT([ac_cv_decl_MAGIC_VERSION], [MAGIC_VERSION], [#include <magic.h>], AC_MSG_FAILURE([failed!]))
AC_MSG_RESULT([$ac_cv_decl_MAGIC_VERSION])
AS_VERSION_COMPARE([$ac_cv_decl_MAGIC_VERSION], [518], [], AC_MSG_ERROR([binwalk needs libmagic version 5.19 or higher. Please see http://bugs.gw.com/view.php?id=330.]), [])
AS_VERSION_COMPARE([$ac_cv_decl_MAGIC_VERSION], [519], AC_MSG_ERROR([binwalk needs libmagic version 5.19 or higher.]), [], [])

AC_SUBST(BUILD_C_LIBS, $BUILD_C_LIBS)
AC_SUBST(PYTHON, $PYTHON)
AC_SUBST(SONAME, $SONAME)
AC_SUBST(SOEXT, $SOEXT)
AC_SUBST(PLATFORM, $(uname -s))
AC_SUBST(INSTALL_OPTIONS, $INSTALL_OPTIONS)
AC_CONFIG_FILES([Makefile])
AC_OUTPUT
