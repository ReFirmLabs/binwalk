AC_INIT([SSDEEP],[2.10],[research@jessekornblum.com])
AM_INIT_AUTOMAKE

AC_CONFIG_FILES([Makefile])
AM_CONFIG_HEADER([config.h])

AC_CANONICAL_HOST

AC_PROG_CC
AC_PROG_CXX
AC_LIBTOOL_WIN32_DLL
#AC_PROG_LIBTOOL
AM_PROG_LIBTOOL
AC_PROG_INSTALL

AC_CONFIG_MACRO_DIR([m4])

case $host in
  *-*-*linux*-*) AC_DEFINE([__LINUX__],1,[Linux operating system functions]) ;;
  *-*-mingw32)   LIBS="-liberty $LIBS" && CPPFLAGS="-DUNICODE -D_UNICODE $CPPFLAGS"
esac


# Bring additional directories where things might be found into our
# search path. I don't know why autoconf doesn't do this by default
for spfx in /usr/local /opt/local /sw ; do
    echo checking ${spfx}/include
    if test -d ${spfx}/include; then
        CPPFLAGS="-I${spfx}/include $CPPFLAGS"
        LDFLAGS="-L${spfx}/lib $LDFLAGS"
    fi
done

AC_C_BIGENDIAN
AC_SYS_LARGEFILE

AC_CHECK_HEADERS([libgen.h])
AC_CHECK_HEADERS([dirent.h])
AC_CHECK_HEADERS([inttypes.h])

AC_CHECK_HEADERS([fcntl.h sys/types.h sys/ioctl.h sys/param.h wchar.h unistd.h sys/stat.h sys/disk.h])

AC_CHECK_HEADER([inttypes.h],,AC_MSG_ERROR([You must have inttypes.h or some other C99 equivalent]),)

# These includes are required on FreeBSD
AC_CHECK_HEADERS([sys/mount.h],[],[],
[#ifdef HAVE_SYS_TYPES_H
 # include <sys/types.h>
 #endif
 #ifdef HAVE_SYS_PARAM_H
 # include <sys/param.h>
 #endif])

AC_FUNC_FSEEKO

AC_OUTPUT


