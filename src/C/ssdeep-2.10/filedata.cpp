// SSDEEP
// $Id: filedata.cpp 163 2012-07-17 19:59:54Z jessekornblum $
// Copyright (C) 2012 Kyrus. See COPYING for details.

#ifdef HAVE_CONFIG_H
# include "config.h"
#endif

#include "filedata.h"
#include <stdio.h>
#include <stdarg.h>
#include <string.h>


bool Filedata::valid(void) const
{
  // A valid fuzzy hash has the form
  // [blocksize]:[sig1]:[sig2]
  // with no filename at the end

  // First find the block size
  const char * sig = m_signature.c_str();
  unsigned int block_size;
  if (-1 == sscanf(sig, "%u:", &block_size))
    return false;

  // Move past the blocksize
  sig = strchr(sig,':');
  if (!sig)
    return false;

  // Move past the first colon and Look for the second colon
  ++sig;
  sig = strchr(sig,':');
  if (!sig)
    return false;

  // Finally, a valid signature does *not* have a filename at the end of it
  sig = strchr(sig,',');
  if (sig)
    return false;

  return true;
}


void Filedata::clear_cluster(void)
{
  if (NULL == m_cluster)
    return;

  // We don't want to call the destructors on the individual elements
  // so we have to clear the set first.
  m_cluster->clear();
  m_cluster = NULL;
}


Filedata::Filedata(const TCHAR *fn, const char * sig, const char * match_file)
{
  m_signature = std::string(sig);
  if (not valid())
    throw std::bad_alloc();

  m_filename = _tcsdup(fn);
  m_cluster  = NULL;

  if (NULL == match_file)
    m_has_match_file = false;
  else
  {
    m_has_match_file = true;
    m_match_file = std::string(match_file);
  }
}


Filedata::Filedata(const std::string sig, const char * match_file)
{
  // Set the easy stuff first
  m_cluster = NULL;

  if (NULL == match_file)
    m_has_match_file = false;
  else
  {
    m_has_match_file = true;
    m_match_file = std::string(match_file);
  }

  // If we don't have a filename included with the sig, that's ok,
  // but we should find out now.
  // If there is a filename, it should be immediately after the
  // first comma and enclosed in quotation marks.
  size_t start, stop;
  start = sig.find_first_of(",\"");
  if (std::string::npos == start)
  {
    // There is no filename. Ok. We still have a valid Filedata.
    m_filename  = _tcsdup(_TEXT("[NO FILENAME]"));
    m_signature = std::string(sig);

    // We still have to check the validity of the signature
    if (not valid())
      throw std::bad_alloc();

    return;
  }
  
  // There is a filename. Ok.
  // Advance past the comma and quotation mark.
  start += 2;
  
  // Look for the second quotation mark, which should be at the end
  // of the string. 
  stop = sig.find_last_of('"');
  if (stop != sig.size() - 1)
    throw std::bad_alloc();
  
  // Strip off the final quotation mark and record the filename
  std::string tmp = sig.substr(start,(stop - start));

  // Strip off the filename from the signature. Remember that "start"
  // now points to two characters ahead of the comma
  m_signature = sig.substr(0,start-2);
  
  // Unescape any quotation marks in the filename
  while (tmp.find(std::string("\\\"")) != std::string::npos)
    tmp.replace(tmp.find(std::string("\\\"")),2,std::string("\""));
  
#ifndef _WIN32
  m_filename = strdup(tmp.c_str());
#else
  char * tmp2 = strdup(tmp.c_str());
  
  // On Win32 we have to do a kludgy cast from ordinary char 
  // values to the TCHAR values we use internally. Because we may have
  // reset the string length, get it again.
  // The extra +1 is for the terminating newline
  size_t i, sz = strlen(tmp2);
  m_filename = (TCHAR *)malloc(sizeof(TCHAR) * (sz + 1));
  if (NULL == m_filename)
    throw std::bad_alloc();

  for (i = 0 ; i < sz ; i++)
    m_filename[i] = (TCHAR)(tmp2[i]);
  m_filename[i] = 0;
#endif
}


std::ostream& operator<<(std::ostream& o, const Filedata& f)
{
  return o << f.get_signature() << "," << f.get_filename() << ",";
}


bool operator==(const Filedata& a, const Filedata& b)
{
  if (a.get_signature() != b.get_signature())
    return false;
  if (a.has_match_file() and not b.has_match_file())
    return false;
  if (not a.has_match_file() and b.has_match_file())
    return false;
  if (a.has_match_file() and b.has_match_file())
  {
    if (a.get_match_file() != b.get_match_file())
      return false;
  }

  return true;
}

