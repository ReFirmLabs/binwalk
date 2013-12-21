#ifndef __SSDEEP_H
#define __SSDEEP_H

// Fuzzy Hashing by Jesse Kornblum
// Copyright (C) 2013 Facebook
// Copyright (C) 2012 Kyrus
// Copyright (C) 2008 ManTech International Corporation
//
// $Id: ssdeep.h 190 2013-07-11 00:40:22Z jessekornblum $
//

#include "main.h"

#include <string>
#include <map>
#include <set>
#include <vector>

#include "fuzzy.h"
#include "tchar-local.h"
#include "filedata.h"

// This is a kludge, but it works.
#define __progname "ssdeep"

#define SSDEEPV1_0_HEADER        "ssdeep,1.0--blocksize:hash:hash,filename"
#define SSDEEPV1_1_HEADER        "ssdeep,1.1--blocksize:hash:hash,filename"
#define OUTPUT_FILE_HEADER     SSDEEPV1_1_HEADER

// We print a warning for files smaller than this size
#define SSDEEP_MIN_FILE_SIZE   4096

// The default 'PATH_MAX' on Windows is about 255 bytes. We can expand
// this limit to 32,767 characters by prepending filenames with "\\?\"
#define SSDEEP_PATH_MAX 32767

#define MD5DEEP_ALLOC(TYPE,VAR,SIZE)     \
VAR = (TYPE *)malloc(sizeof(TYPE) * SIZE);  \
if (NULL == VAR)  \
   return EXIT_FAILURE; \
memset(VAR,0,SIZE * sizeof(TYPE));


// These are the types of files we can encounter while hashing
#define file_regular    0
#define file_directory  1
#define file_door       2
#define file_block      3
#define file_character  4
#define file_pipe       5
#define file_socket     6
#define file_symlink    7
#define file_unknown  254


typedef struct _filedata_t
{
  uint64_t id;

  /// Original signature in the form [blocksize]:[sig1]:[sig2]
  std::string signature;

  uint64_t blocksize;

  /// Holds signature equal to blocksize
  std::string s1;
  /// Holds signature equal to blocksize * 2
  std::string s2;

  TCHAR * filename;

  /// File of hashes where we got this known file from.
  std::string match_file;

  /// Cluster which contains this file
  std::set<_filedata_t> * cluster;

} filedata_t;


typedef struct {
  uint64_t  mode;

  bool       first_file_processed;

  // Known hashes
  std::vector<Filedata *> all_files;

  // Known clusters
  std::set< std::set<Filedata *> * > all_clusters;

  /// Display files who score above the threshold
  uint8_t   threshold;

  bool       found_meaningful_file;
  bool       processed_file;

  int       argc;
  TCHAR     **argv;

  /// Current line number in file of known hashes
  uint64_t line_number;
  /// File handle to file of known hashes
  FILE     * known_handle;
  /// Filename of known hashes
  char     * known_fn;

} state;



#define MM_INIT  printf

// Things required when cross compiling for Microsoft Windows
#ifdef _WIN32

// We create macros for the Windows equivalent UNIX functions.
// No worries about lstat to stat; Windows doesn't have symbolic links
#define lstat(A,B)      stat(A,B)
#define realpath(A,B)   _fullpath(B,A,PATH_MAX)
#define snprintf        _snprintf

char *basename(char *a);
extern char *optarg;
extern int optind;
int getopt(int argc, char *const argv[], const char *optstring);

#define NEWLINE        "\r\n"
#define DIR_SEPARATOR  '\\'

#else   // ifdef _WIN32
// For all other operating systems

#define NEWLINE       "\n"
#define DIR_SEPARATOR '/'

#endif  // ifdef _WIN32/else





// Because the modes are stored in a uint64_t variable, they must
// be less than or equal to 1<<63
#define mode_none            0
#define mode_recursive       1
#define mode_match        1<<1
#define mode_barename     1<<2
#define mode_relative     1<<3
#define mode_silent       1<<4
#define mode_directory    1<<5
#define mode_match_pretty 1<<6
#define mode_verbose      1<<7
#define mode_csv          1<<8
#define mode_threshold    1<<9
#define mode_sigcompare   1<<10
#define mode_display_all  1<<11
#define mode_compare_unknown 1<<12
#define mode_cluster      1<<13
#define mode_recursive_cluster 1<<14

#define MODE(A)   (s->mode & A)

#define BLANK_LINE   \
"                                                                               "



// *********************************************************************
// Checking for cycles
// *********************************************************************
int done_processing_dir(TCHAR *fn);
int processing_dir(TCHAR *fn);
int have_processed_dir(TCHAR *fn);

bool process_win32(state *s, TCHAR *fn);
int process_normal(state *s, TCHAR *fn);
int process_stdin(state *s);


// *********************************************************************
// Fuzzy Hashing Engine
// *********************************************************************
int hash_file(state *s, TCHAR *fn);
bool display_result(state *s, const TCHAR * fn, const char * sum);


// *********************************************************************
// Helper functions
// *********************************************************************
void try_msg(void);

bool expanded_path(TCHAR *p);

void sanity_check(state *s, int condition, const char *msg);

// The basename function kept misbehaving on OS X, so I rewrote it.
// This function isn't perfect, nor is it designed to be. Because
// we're guarenteed to be working with a filename here, there's no way
// that s will end with a DIR_SEPARATOR (e.g. /foo/bar/). This function
// will not work properly for a string that ends in a DIR_SEPARATOR
int my_basename(TCHAR *s);
int my_dirname(TCHAR *s);

// Remove the newlines, if any, from the string. Works with both
// \r and \r\n style newlines
void chop_line_tchar(TCHAR *s);
void chop_line(char *s);

int find_comma_separated_string_tchar(TCHAR *s, unsigned int n);
void shift_string_tchar(TCHAR *fn, unsigned int start, unsigned int new_start);

int find_comma_separated_string(char *s, unsigned int n);
void shift_string(char *fn, size_t start, size_t new_start);

int remove_escaped_quotes(char * str);

void prepare_filename(state *s, TCHAR *fn);

// Returns the size of the given file, in bytes.

#ifdef __cplusplus
extern "C" {
#endif

off_t find_file_size(FILE *h);

#ifdef __cplusplus
}
#endif



// *********************************************************************
// User Interface Functions
// *********************************************************************
void print_status(const char *fmt, ...);
void print_error(const state *s, const char *fmt, ...);
void print_error_unicode(state *s, const TCHAR *fn, const char *fmt, ...);
void internal_error(const char *fmt, ... );
void fatal_error(const char *fmt, ... );
void display_filename(FILE *out, const TCHAR *fn, int escape_quotes);



#endif  // #ifndef __SSDEEP_H
