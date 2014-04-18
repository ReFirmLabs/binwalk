// MD5DEEP - dig.c
//
// By Jesse Kornblum
//
// This is a work of the US Government. In accordance with 17 USC 105,
// copyright protection is not available for any work of the US Government.
//
// This program is distributed in the hope that it will be useful, but
// WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
//
// $Id: dig.cpp 191 2013-07-16 17:55:00Z jessekornblum $

#include "ssdeep.h"

#define STATUS_OK   FALSE

static int is_special_dir(TCHAR *d)
{
  return ((!_tcsncmp(d,_TEXT("."),1) && (_tcslen(d) == 1)) ||
          (!_tcsncmp(d,_TEXT(".."),2) && (_tcslen(d) == 2)));
}

#ifndef _WIN32

static TCHAR DOUBLE_DIR[4] =
  { (TCHAR)DIR_SEPARATOR,
    (TCHAR)DIR_SEPARATOR,
    0
  };

static void remove_double_slash(TCHAR *fn)
{
  size_t tsize = sizeof(TCHAR);
  TCHAR *tmp = fn, *new_str;

  new_str = _tcsstr(tmp,DOUBLE_DIR);
  while (NULL != new_str)
  {
    /*
#ifdef _WIN32
    // On Windows, we have to allow the first two characters to be slashes
    // to account for UNC paths. e.g. \\SERVER\dir\path
    if (tmp == fn)
    {
      ++tmp;
    }
    else
    {
#endif  // ifdef _WIN32
    */
      _tmemmove(new_str,new_str+tsize,_tcslen(new_str));

      /*
#ifdef _WIN32
    }
#endif  // ifdef _WIN32
      */

    new_str = _tcsstr(tmp,DOUBLE_DIR);
  }
}


static void remove_single_dirs(TCHAR *fn)
{
  unsigned int pos, chars_found = 0;
  size_t sz = _tcslen(fn), tsize = sizeof(TCHAR);

  for (pos = 0 ; pos < sz ; pos++)
  {
    // Catch strings that end with /. (e.g. /foo/.)
    if (pos > 0 &&
	fn[pos-1] == _TEXT(DIR_SEPARATOR) &&
	fn[pos]   == _TEXT('.') &&
	fn[pos+1] == 0)
      fn[pos] = 0;

    if (fn[pos] == _TEXT('.') && fn[pos+1] == _TEXT(DIR_SEPARATOR))
    {
      if (chars_found && fn[pos-1] == _TEXT(DIR_SEPARATOR))
      {
	_tmemmove(fn+(pos*tsize),(fn+((pos+2)*tsize)),(sz-pos) * tsize);

	// In case we have ././ we shift back one!
	--pos;

      }
    }
    else
      ++chars_found;
  }
}

// Removes all "../" references from the absolute path fn
void remove_double_dirs(TCHAR *fn)
{
  size_t pos, next_dir, sz = _tcslen(fn), tsize = sizeof(TCHAR);

  for (pos = 0; pos < _tcslen(fn) ; pos++)
  {
    if (fn[pos] == _TEXT('.') && fn[pos+1] == _TEXT('.'))
    {
      if (pos > 0)
      {

	/* We have to keep this next if statement and the one above separate.
	   If not, we can't tell later on if the pos <= 0 or
	   that the previous character was a DIR_SEPARATOR.
	   This matters when we're looking at ..foo/ as an input */

	if (fn[pos-1] == _TEXT(DIR_SEPARATOR))
	{

	  next_dir = pos + 2;

	  /* Back up to just before the previous DIR_SEPARATOR
	     unless we're already at the start of the string */
	  if (pos > 1)
	    pos -= 2;
	  else
	    pos = 0;

	  while (fn[pos] != _TEXT(DIR_SEPARATOR) && pos > 0)
	    --pos;

	  switch(fn[next_dir])
	  {
	  case DIR_SEPARATOR:
	    _tmemmove(fn+pos,fn+next_dir,((sz - next_dir) + 1) * tsize);
	    break;

	  case 0:
	    /* If we have /.. ending the filename */
	    fn[pos+1] = 0;
	    break;

	    /* If we have ..foo, we should do nothing, but skip
	       over these double dots */
	  default:
	    pos = next_dir;
	  }
	}
      }

      /* If we have two dots starting off the string, we should prepend
	 a DIR_SEPARATOR and ignore the two dots. That is:
	 from the root directory the path ../foo is really just /foo */

      else
      {
	fn[pos] = _TEXT(DIR_SEPARATOR);
	_tmemmove(fn+pos+1,fn+pos+3,sz-(pos+3));


      }
    }
  }
}


// We don't need to call these functions when running in Windows
// as we've already called real_path() on them in main.c. These
// functions are necessary in *nix so that we can clean up the
// path names without removing the names of symbolic links. They
// are also called when the user has specified an absolute path
// but has included extra double dots or such.

static void clean_name(state *s, TCHAR *fn)
{
  if (not (s->mode & mode_relative)) {
    remove_double_slash(fn);
    remove_single_dirs(fn);
    remove_double_dirs(fn);
  }
}


static int process_dir(state *s, TCHAR *fn)
{
  int return_value = STATUS_OK;
  TCHAR *new_file;
  _TDIR *current_dir;
  struct _tdirent *entry;

  if (have_processed_dir(fn))
  {
    print_error_unicode(s,fn,"symlink creates cycle");
    return STATUS_OK;
  }

  if (!processing_dir(fn))
    internal_error("%s: Cycle checking failed to register directory.", fn);

  if ((current_dir = _topendir(fn)) == NULL)
  {
    print_error_unicode(s,fn,"%s", strerror(errno));
    return STATUS_OK;
  }

  new_file = (TCHAR *)malloc(sizeof(TCHAR) * SSDEEP_PATH_MAX);
  if (NULL == new_file)
    internal_error("%s: Out of memory", __progname);

  while ((entry = _treaddir(current_dir)) != NULL)
  {
    if (is_special_dir(entry->d_name))
      continue;

    _sntprintf(new_file,SSDEEP_PATH_MAX,_TEXT("%s%c%s"),
	       fn,DIR_SEPARATOR,entry->d_name);

    return_value = process_normal(s,new_file);
  }

  free(new_file);
  _tclosedir(current_dir);

  if (!done_processing_dir(fn))
    internal_error("%s: Cycle checking failed to unregister directory.", fn);

  return return_value;
}


static int file_type_helper(_tstat_t sb)
{
  if (S_ISREG(sb.st_mode))
    return file_regular;

  if (S_ISDIR(sb.st_mode))
    return file_directory;

  if (S_ISBLK(sb.st_mode))
    return file_block;

  if (S_ISCHR(sb.st_mode))
    return file_character;

  if (S_ISFIFO(sb.st_mode))
    return file_pipe;

  /* These file types do not exist in Win32 */
#ifndef _WIN32

  if (S_ISSOCK(sb.st_mode))
    return file_socket;

  if (S_ISLNK(sb.st_mode))
    return file_symlink;
#endif   /* ifndef _WIN32 */


  /* Used to detect Solaris doors */
#ifdef S_IFDOOR
#ifdef S_ISDOOR
  if (S_ISDOOR(sb.st_mode))
    return file_door;
#endif
#endif

  return file_unknown;
}


static int file_type(state *s, TCHAR *fn)
{
  _tstat_t sb;

  if (NULL == s || NULL == fn)
    return file_unknown;

  if (_lstat(fn,&sb))
  {
    print_error_unicode(s,fn,"%s", strerror(errno));
    return file_unknown;
  }

  return file_type_helper(sb);
}


static int should_hash_symlink(state *s, TCHAR *fn, int *link_type)
{
  int type;
  _tstat_t sb;

  if (NULL == s || NULL == fn)
    fatal_error("%s: Null state passed into should_hash_symlink", __progname);

  // We must look at what this symlink points to before we process it.
  // The normal file_type function uses lstat to examine the file,
  // we use stat to examine what this symlink points to.
  if (_sstat(fn,&sb))
    {
      print_error_unicode(s,fn,"%s",strerror(errno));
      return FALSE;
    }

  type = file_type_helper(sb);

  if (type == file_directory)
    {
      if (s->mode & mode_recursive)
	process_dir(s,fn);
      else
	{
	  print_error_unicode(s,fn,"Is a directory");
	}
      return FALSE;
    }

  if (link_type != NULL)
    *link_type = type;
  return TRUE;
}


#define RETURN_IF_MODE(A) \
if (s->mode & A) \
  return TRUE; \
break;


static int should_hash(state *s, TCHAR *fn)
{
  int type = file_type(s, fn);

  if (NULL == s || NULL == fn)
    fatal_error("%s: Null state passed into should_hash", __progname);

  if (type == file_directory)
  {
    if (s->mode & mode_recursive)
      process_dir(s,fn);
    else
    {
      print_error_unicode(s,fn,"Is a directory");
    }
    return FALSE;
  }

  if (type == file_symlink)
    return should_hash_symlink(s,fn,NULL);

  if (type == file_unknown)
    return FALSE;

  // By default we hash anything we can't identify as a "bad thing"
  return TRUE;
}


int process_normal(state *s, TCHAR *fn)
{
  clean_name(s,fn);

  if (should_hash(s,fn))
    return (hash_file(s,fn));

  return FALSE;
}
#endif   // ifndef _WIN32


/// The largest number of bytes we can process from stdin
/// This limit is arbitrary and can be adjusted at will
#define MAX_STDIN_BUFFER      536870912
#define MAX_STDIN_BUFFER_STR  "512 MB"

int process_stdin(state *s)
{
  if (NULL == s)
    return TRUE;

  char sum[FUZZY_MAX_RESULT];
  unsigned char * buffer = (unsigned char *)malloc(sizeof(unsigned char ) * MAX_STDIN_BUFFER);
  if (NULL == buffer)
    return TRUE;
  memset(buffer,0,MAX_STDIN_BUFFER);

  size_t sz = fread(buffer, 1, MAX_STDIN_BUFFER, stdin);
  if (MAX_STDIN_BUFFER == sz)
  {
    print_error(s,
		"%s: Only processed the first %s presented on stdin.",
		__progname,
		MAX_STDIN_BUFFER_STR);
  }

  int status = fuzzy_hash_buf(buffer, (uint32_t)sz, sum);
  free(buffer);

  if (status != 0)
  {
    print_error_unicode(s,_TEXT("stdin"),"Error processing stdin");
    return TRUE;
  }

  display_result(s,_TEXT("stdin"),sum);

  return FALSE;
}




#ifdef _WIN32
static int is_win32_device_file(TCHAR *fn)
{
  /* Specifications for device files came from
     http://msdn.microsoft.com/library/default.asp?url=/library/en-us/fileio/base/createfile.asp

     -- Physical devices (like hard drives) are
        \\.\PhysicalDriveX where X is a digit from 0 to 9
     -- Tape devices is \\.\tapeX where X is a digit from 0 to 9
     -- Logical volumes is \\.\X: where X is a letter */

  if (!_tcsnicmp(fn, _TEXT("\\\\.\\physicaldrive"),17) &&
      (_tcslen(fn) == 18) &&
      isdigit(fn[17]))
    return TRUE;

  if (!_tcsnicmp(fn, _TEXT("\\\\.\\tape"),8) &&
      (_tcslen(fn) == 9) &&
      isdigit(fn[8]))
    return TRUE;

  if ((!_tcsnicmp(fn,_TEXT("\\\\.\\"),4)) &&
      (_tcslen(fn) == 6) &&
      (isalpha(fn[4])) &&
      (fn[5] == ':'))
    return TRUE;

  return FALSE;
}


bool process_dir_win32(state *s, TCHAR *fn) {
  TCHAR new_fn[SSDEEP_PATH_MAX];

  if (have_processed_dir(fn)) {
    print_error_unicode(s, fn, "Cycle detected");
    return true;
  }

  processing_dir(fn);

  _sntprintf(new_fn,
	     SSDEEP_PATH_MAX,
	     _TEXT("%s\\*"),
	     fn);

  process_win32(s, new_fn);

  done_processing_dir(fn);
  return false;
}


bool process_win32(state *s, TCHAR *fn)
{
  int rc;
  size_t len;
  HANDLE hFind;
  TCHAR dirname[SSDEEP_PATH_MAX], new_fn[SSDEEP_PATH_MAX], expanded_fn[SSDEEP_PATH_MAX];
  WIN32_FIND_DATAW FindFileData;

  if (NULL == s or NULL == fn)
    return true;

  //print_status("process_win32 got %S", fn);

  if (is_win32_device_file(fn))
    return hash_file(s, fn);
  if (is_special_dir(fn))
    return false;

  // Most Win32 programs reject 'c:'
  // as an error or use it to alias the current working directory on c:.
  // As a convenience to users, we're going to accept 'c:'. To do this
  // we change it into 'c:\'
  if (_tcslen(fn) == 2 and isalpha(fn[0]) and fn[1] == _TEXT(':')) {
    fn[2] = _TEXT(DIR_SEPARATOR);
    fn[3] = 0;
  }

  // FindFirstFile doesn't accept '\' as the trailing character.
  // If we get '\' as a trailing character, we assume this is a directory
  // and handle that according. In recursive mode, go through the directory
  // entries. Otherwise, return an error.
  len = _tcslen(fn);
  if (fn[len-1] == _TEXT(DIR_SEPARATOR)) {
    if (s->mode & mode_recursive) {
      fn[len]   = _TEXT('*');
      fn[len+1] = 0;
    } else {
      print_error_unicode(s, fn, "Is a directory");
      return false;
    }
  }

  //print_status("cleaned name %S", fn);

  // If we don't have it already, create the expanded filename.
  // "C:\foo\bar.txt" --> "\\?\C:\foo\bar.txt"
  if (not expanded_path(fn) and
      not (s->mode & mode_relative)) {
    _sntprintf(expanded_fn,
	       SSDEEP_PATH_MAX,
	       _TEXT("\\\\?\\%s"),
	       fn);
  }
  else {
    _tcsncpy(expanded_fn, fn, SSDEEP_PATH_MAX);
  }
  //print_status("expanded filename %S", expanded_fn);

  hFind = FindFirstFile(expanded_fn, &FindFileData);
  if (INVALID_HANDLE_VALUE == hFind)
  {
    // We don't display an error if there was a wildcard anywhere in the
    // original filename, e.g. C:\foo\*. When this happens it means we just
    // didn't find any matching files.
    // Note that we still display errors with the original 'fn'
    if (not _tcsstr(fn, _TEXT("*")))
      print_error_unicode(s, fn, "No such file or directory");
    return false;
  }

  _tcsncpy(dirname, fn, SSDEEP_PATH_MAX);
  my_dirname(dirname);

  do {
    // The filename we've found doesn't include any path information.
    // That is, for the file C:\foo\bar.txt, we have bar.txt.
    // We have to add the path information back in manually.
    // Thankfully Windows doesn't allow wildcards in the early part
    // of the path. For example, we will never see:  c:\bin\*\tools
    //
    // Because the wildcard is always in the last part of the input
    // (e.g. c:\bin\*.exe) we can use the original dirname, combined
    // with the filename we've found, to make the new filename.
    if (not is_special_dir(FindFileData.cFileName)) {

      //      print_status("Found file: %S", FindFileData.cFileName);

      _sntprintf(new_fn,
		 SSDEEP_PATH_MAX,
		 _TEXT("%s%s"),
		 dirname,
		 FindFileData.cFileName);
      if (not expanded_path(new_fn) and
	  not (s->mode & mode_relative)) {
	_sntprintf(expanded_fn,
		   SSDEEP_PATH_MAX,
		   _TEXT("\\\\?\\%s"),
		   new_fn);
      } else {
	_tcsncpy(expanded_fn, new_fn, SSDEEP_PATH_MAX);
      }

      //      print_status("Getting attributes for %S", expanded_fn);
      DWORD dwFileAttributes = FindFileData.dwFileAttributes;

      if (INVALID_FILE_ATTRIBUTES == dwFileAttributes) {
	print_error_unicode(s, new_fn, "File read error");
      } else if (dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) {
	if (s->mode & mode_recursive) {
	  process_dir_win32(s, new_fn);
	}

      // TODO Add support for symbolic links
      /*
      } else if (dwFileAttributes & FILE_ATTRIBUTE_REPARSE_POINT) {
	// Generally we skip reparse points (e.g. symbolic links,
	// junction points, etc) UNLESS it's part of single
	// instance storage. Single Instance Storage "is a system's
	// ability to keep one copy of content that multiple users
	// or computers share". See
	// http://blogs.technet.com/b/filecab/archive/2006/02/03/single-instance-store-sis-in-windows-storage-server-r2.aspx
	switch (FindFileData.dwReserved0) {
	case IO_REPARSE_TAG_MOUNT_POINT:
	  print_error_unicode(s, new_fn, "Junction point, skipping.");
	  break;

	case IO_REPARSE_TAG_SYMLINK:
	  print_error_unicode(s, new_fn, "Symbolic link, skipping.");
	  break;

	case IO_REPARSE_TAG_SIS:
	  hash_file(s, new_fn);
	  break;

	default:
	  print_error_unicode(s,
			      new_fn,
			      "Unknown reparse point 0x%"PRIx32", skipping. Please report this to the developers",
			      FindFileData.dwReserved0);
	  break;
	}
      */

      } else {
	hash_file(s, new_fn);
      }
    }

    rc = FindNextFile(hFind, &FindFileData);
  } while (rc != 0);

  if (GetLastError() != ERROR_NO_MORE_FILES) {
    // The Windows API for getting an intelligible error message
    // is beserk. Rather than play their silly games, we
    // acknowledge that an unknown error occured and hope we
    // can continue.
    print_error_unicode(s, new_fn, "Unknown error during directory traversal");
    return true;
  }

  rc = FindClose(hFind);
  if (0 == rc) {
    print_error_unicode(s, fn, "Unknown error cleaning up directory traversal");
  }

  return false;
}
#endif
