
/* $Id: tchar-local.h 61 2008-02-22 23:18:59Z jessekornblum $ */

#ifndef __TCHAR_LOCAL_H
#define __TCHAR_LOCAL_H


/* Unicode support */
#ifdef _WIN32

// This says that we require Windows NT 4.0 to run
#define _WIN32_WINNT 0x0400

# include <windows.h>
# include <wchar.h>
# include <tchar.h>

/* The PRINTF_S character is used in situations where we have a string
   with one TCHAR and one char argument. It's impossible to use the
   _TEXT macro because we don't know which will be which. */
#define  PRINTF_S   "S"

#define _tmemmove      wmemmove

/* The Win32 API does have lstat, just stat. As such, we don't have to
   worry about the difference between the two. */
#define _lstat         _tstat
#define _sstat         _tstat
#define _tstat_t       struct _stat



#else  // ifdef _WIN32


#define  PRINTF_S   "s"

/* The next few paragraphs are similar to tchar.h when UNICODE
   is not defined. They define all of the _t* functions to use
   the standard char * functions. This works just fine on Linux and OS X */
#define  TCHAR      char

#define  _TDIR      DIR
#define  _TEXT(A)   A

#define  _sntprintf snprintf
#define  _tprintf   printf
#define  _ftprintf  fprintf

#define  _lstat     lstat
#define  _sstat     stat
#define  _tstat_t   struct stat

#define  _tgetcwd   getcwd
#define  _tfopen    fopen
#define  _fgetts    fgets

#define  _topendir  opendir
#define  _treaddir  readdir
#define  _tdirent   dirent
#define  _tclosedir closedir

#define  _tcsncpy   strncpy
#define  _tcslen    strlen
#define  _tcsnicmp  strncasecmp
#define  _tcsncmp   strncmp
#define  _tcsrchr   strrchr
#define  _tmemmove  memmove
#define  _tcsdup    strdup
#define  _tcsstr    strstr

#endif


#endif //   __TCHAR_LOCAL_H
