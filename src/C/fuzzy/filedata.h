#ifndef __FILEDATA_H
#define __FILEDATA_H

/// @file filedata.h
// Copyright (C) 2012 Kyrus. See COPYING for details

// $Id: filedata.h 160 2012-07-17 01:00:07Z jessekornblum $

#include <set>
#include <string>
#include <iostream>
#include "tchar-local.h"

/// Contains a fuzzy hash and associated metadata for file
class Filedata
{
 public:
 Filedata() : m_has_match_file(false) {}

  /// Creates a new Filedata object with the given filename and signature
  ///
  /// If sig is not valid, throws std::bad_alloc
  Filedata(const TCHAR * fn, const char * sig, const char * match_file = NULL);

  /// Creates a new Filedata object with the given filename and signature
  ///
  /// If sig is not valid, throws std::bad_alloc
  Filedata(const std::string sig, const char * match_file = NULL);

  /// Returns the file's fuzzy hash without a filename. 
  /// std::string("[blocksize]:[sig1]:[sig2]")
  std::string get_signature(void) const { return m_signature; }

  /// Returns the file's name
  /// RBF - Should this be a std::wstring?
  TCHAR * get_filename(void) const { return m_filename; }

  /// Returns true if this file came from a file of known files on the disk
  bool has_match_file(void) const { return m_has_match_file; }
  /// Returns the name of the file on the disk from which this file came
  /// RBF - Should this be a std::wstring?
  std::string get_match_file(void) const { return m_match_file; }

  /// Returns true if this file belongs to a cluster of similar files
  bool has_cluster(void) const { return (m_cluster != NULL); }
  void set_cluster(std::set<Filedata *> *c) { m_cluster = c; }
  std::set<Filedata* >* get_cluster(void) const { return m_cluster; }
  void clear_cluster(void);

 private:
  std::set<Filedata *> * m_cluster;

  /// Original signature in the form [blocksize]:[sig1]:[sig2]
  /// It may also contain the filename, but there is no guarantee of that
  /// one way or the other.
  std::string m_signature;

  /// RBF - Should this be a std::wstring?
  TCHAR * m_filename;

  /// File of hashes where we got this known file from, if any
  std::string m_match_file;
  bool m_has_match_file;

  /// Returns true if the m_signature field contains a valid fuzzy hash
  bool valid(void) const;
};


/// Display [blocksize]:[sig1]:[sig2],"filename"
std::ostream& operator<<(std::ostream& o, const Filedata& f);

/// RBF - We can use this IF AND ONLY IF get_filename() returns a std::wstring
//bool operator==(const Filedata& a, const Filedata& b);

#endif  // ifndef __FILEDATA_H
