// ssdeep
// Copyright (C) 2012 Kyrus
// Copyright (C) 2006 ManTech International Corporation
//
// $Id: helpers.cpp 184 2013-07-10 05:24:26Z jessekornblum $
//
// This program is free software; you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation; either version 2 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// 
// You should have received a copy of the GNU General Public License
// along with this program; if not, write to the Free Software
// Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA


#include "ssdeep.h"

void try_msg(void)
{
  fprintf (stderr,"Try `%s -h` for more information.%s", __progname, NEWLINE);
}


bool expanded_path(TCHAR *p)
{
  if (_tcsncmp(p,_TEXT("\\\\?\\"),4))
    return false;
  return true;
}


void sanity_check(state *s, int condition, const char *msg)
{
  if (NULL == s)
    exit(EXIT_FAILURE);
  
  if (condition)
    {
      if (!(s->mode & mode_silent))
	{
	  print_status("%s: %s", __progname, msg);
	  try_msg();
	}
      exit (EXIT_FAILURE);
    }
}


// The basename function kept misbehaving on OS X, so I rewrote it.
// This function isn't perfect, nor is it designed to be. Because
// we're guaranteed to be working with a filename here, there's no way
// that s will end with a DIR_SEPARATOR (e.g. /foo/bar/). This function
// will not work properly for a string that ends in a DIR_SEPARATOR */
int my_basename(TCHAR *s)
{
  size_t len;
  TCHAR * tmp;

  if (NULL == s)
    return TRUE;

  tmp = _tcsrchr(s,DIR_SEPARATOR);

  if (NULL == tmp)
    return FALSE;

  len = _tcslen(tmp);

  // We advance tmp one character to move us past the DIR_SEPARATOR
  _tmemmove(s,tmp+1,len);

  return FALSE;
}


int my_dirname(TCHAR *c)
{
  TCHAR *tmp;

  if (NULL == c)
    return TRUE;

  // If there are no DIR_SEPARATORs in the directory name, then the 
  // directory name should be the empty string 
  tmp = _tcsrchr(c,DIR_SEPARATOR);
  if (NULL != tmp)
    tmp[1] = 0;
  else
    c[0] = 0;

  return FALSE;
}





void prepare_filename(state *s, TCHAR *fn)
{
  if (s->mode & mode_barename)
  {
    if (my_basename(fn))
    {
      print_error_unicode(s,fn,"Unable to shorten filename");
      return;
    }
  }
}


 



// Remove the newlines, if any. Works on both DOS and *nix newlines
void chop_line_tchar(TCHAR *s)
{
  size_t pos = _tcslen(s);

  while (pos > 0) 
  {
    // We split up the two checks because we can never know which
    // condition the computer will examine if first. If pos == 0, we
    // don't want to be checking s[pos-1] under any circumstances! 

    if (!(s[pos-1] == _TEXT('\r') || s[pos-1] == _TEXT('\n')))
      return;

    s[pos-1] = 0;
    --pos;
  }
}


// Remove the newlines, if any. Works on both DOS and *nix newlines
void chop_line(char *s)
{
  size_t pos = strlen(s);

  while (pos > 0) 
  {
    // We split up the two checks because we can never know which
    // condition the computer will examine if first. If pos == 0, we
    // don't want to be checking s[pos-1] under any circumstances! 

    if (!(s[pos-1] == _TEXT('\r') || s[pos-1] == _TEXT('\n')))
      return;

    s[pos-1] = 0;
    --pos;
  }
}


// Shift the contents of a string so that the values after 'new_start'
// will now begin at location 'start' 
void shift_string_tchar(TCHAR *fn, unsigned int start, unsigned int new_start)
{
  size_t sz = _tcslen(fn);

  if (start > sz || new_start < start)
    return;

  while (new_start < sz)
    {
      fn[start] = fn[new_start];
      new_start++;
      start++;
    }

  fn[start] = 0;
}



// Find the index of the next comma in the string s starting at index start.
// If there is no next comma, returns -1.
int find_next_comma_tchar(TCHAR *s, unsigned int start)
{
  size_t size = _tcslen(s);
  unsigned int pos = start;
  int in_quote = FALSE;

  while (pos < size)
  {
    switch (s[pos]) {
    case _TEXT('"'):
      in_quote = !in_quote;
      break;
    case _TEXT(','):
      if (in_quote)
        break;

    // Although it's potentially unwise to cast an unsigned int back
    // to an int, problems will only occur when the value is beyond
    // the range of int. Because we're working with the index of a
    // string that is probably less than 32,000 characters, we should
    // be okay. 
      return (int)pos;
    }
    ++pos;
  }
  return -1;
}

void mm_magic(void){MM_INIT("%s\n","\x49\x20\x64\x6f\x20\x6e\x6f\x74\x20\x62\x65\x6c\x69\x65\x76\x65\x20\x77\x65\x20\x77\x69\x6c\x6c\x20\x67\x65\x74\x20\x45\x64\x64\x69\x65\x20\x56\x61\x6e\x20\x48\x61\x6c\x65\x6e\x20\x75\x6e\x74\x69\x6c\x20\x77\x65\x20\x68\x61\x76\x65\x20\x61\x20\x74\x72\x69\x75\x6d\x70\x68\x61\x6e\x74\x20\x76\x69\x64\x65\x6f\x2e");}


// Returns the string after the nth comma in the string s. If that
// string is quoted, the quotes are removed. If there is no valid
// string to be found, returns TRUE. Otherwise, returns FALSE 
int find_comma_separated_string_tchar(TCHAR *s, unsigned int n)
{
  int start = 0, end;
  unsigned int count = 0;
  while (count < n)
  {
    if ((start = find_next_comma_tchar(s,start)) == -1)
      return TRUE;
    ++count;
    // Advance the pointer past the current comma
    ++start;
  }

  // It's okay if there is no next comma, it just means that this is
  // the last comma separated value in the string 
  if ((end = find_next_comma_tchar(s,start)) == -1)
    end = _tcslen(s);

  // Strip off the quotation marks, if necessary. We don't have to worry
  // about uneven quotation marks (i.e quotes at the start but not the end
  // as they are handled by the the find_next_comma function. 
  if (s[start] == _TEXT('"'))
    ++start;
  if (s[end - 1] == _TEXT('"'))
    end--;

  s[end] = 0;
  shift_string_tchar(s,0,start);

  return FALSE;
}



// Shift the contents of a string so that the values after 'new_start'
// will now begin at location 'start' 
void shift_string(char *fn, size_t start, size_t new_start)
{
  // TODO: Can shift_string be replaced with memmove? 
  if (start > strlen(fn) || new_start < start)
    return;

  while (new_start < strlen(fn))
    {
      fn[start] = fn[new_start];
      new_start++;
      start++;
    }

  fn[start] = 0;
}


// Find the index of the next comma in the string s starting at index start.
// If there is no next comma, returns -1
int find_next_comma(char *s, unsigned int start)
{
  size_t size=strlen(s);
  unsigned int pos = start; 
  int in_quote = FALSE;
  
  while (pos < size)
    {
      switch (s[pos]) {
      case '"':
	in_quote = !in_quote;
	break;
      case ',':
	if (in_quote)
	  break;

	// Although it's potentially unwise to cast an unsigned int back
	// to an int, problems will only occur when the value is beyond 
	// the range of int. Because we're working with the index of a 
	// string that is probably less than 32,000 characters, we should
	// be okay.
	return (int)pos;
      }
      ++pos;
    }
  return -1;
}


/// Returns the string after the nth comma in the string s. If that
/// string is quoted, the quotes are removed. If there is no valid 
/// string to be found, returns TRUE. Otherwise, returns FALSE 
int find_comma_separated_string(char *s, unsigned int n)
{
  int start = 0, end;
  unsigned int count = 0; 
  while (count < n)
    {
      if ((start = find_next_comma(s,start)) == -1)
	return TRUE;
      ++count;
      // Advance the pointer past the current comma
      ++start;
    }

  // It's okay if there is no next comma, it just means that this is
  // the last comma separated value in the string 
  if ((end = find_next_comma(s,start)) == -1)
    end = strlen(s);

  // Strip off the quotation marks, if necessary. We don't have to worry
  // about uneven quotation marks (i.e quotes at the start but not the end
  // as they are handled by the the find_next_comma function.
  if (s[start] == '"')
    ++start;
  if (s[end - 1] == '"')
    end--;

  s[end] = 0;
  shift_string(s,0,start);
  
  return FALSE;
}



int remove_escaped_quotes(char * str)
{
  if (NULL == str)
    return TRUE;
  
  size_t pos = 0;
  while (str[pos] != 0)
  {
    if ('\\' == str[pos] && '"' == str[pos+1])
      shift_string(str,pos,pos+1);
    
    ++pos;
  }
  
  return FALSE;
}
  


