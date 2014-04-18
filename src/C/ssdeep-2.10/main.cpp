// Fuzzy Hashing by Jesse Kornblum
// Copyright (C) 2013 Facebook
// Copyright (C) 2012 Kyrus
// Copyright (C) 2010 ManTech International Corporation
//
// $Id: main.cpp 187 2013-07-10 06:56:14Z jessekornblum $
//
// This program is licensed under version 2 of the GNU Public License.
// See the file COPYING for details. 

#include "ssdeep.h"
#include "match.h"

#ifdef _WIN32 
// This can't go in main.h or we get multiple definitions of it
// Allows us to open standard input in binary mode by default 
// See http://gnuwin32.sourceforge.net/compile.html for more 
int _CRT_fmode = _O_BINARY;
#endif


static bool initialize_state(state *s)
{
  if (NULL == s)
    return true;

  s->mode                  = mode_none;
  s->first_file_processed  = true;
  s->found_meaningful_file = false;
  s->processed_file        = false;

  s->threshold = 0;

  return false;
}


// In order to fit on one Win32 screen this function should produce
// no more than 22 lines of output.
static void usage(void)
{
  print_status ("%s version %s by Jesse Kornblum", __progname, VERSION);
  print_status ("Copyright (C) 2013 Facebook");
  print_status ("");
  print_status ("Usage: %s [-m file] [-k file] [-dpgvrsblcxa] [-t val] [-h|-V] [FILES]", 
	  __progname);

  print_status ("-m - Match FILES against known hashes in file");
  print_status ("-k - Match signatures in FILES against signatures in file");
  print_status ("-d - Directory mode, compare all files in a directory");
  print_status ("-p - Pretty matching mode. Similar to -d but includes all matches");
  print_status ("-g - Cluster matches together");
  print_status ("-v - Verbose mode. Displays filename as its being processed");
  print_status ("-r - Recursive mode");

  print_status ("-s - Silent mode; all errors are supressed");
  print_status ("-b - Uses only the bare name of files; all path information omitted");
  print_status ("-l - Uses relative paths for filenames");
  print_status ("-c - Prints output in CSV format");
  print_status ("-x - Compare FILES as signature files");
  print_status ("-a - Display all matches, regardless of score");

  print_status ("-t - Only displays matches above the given threshold");

  print_status ("-h - Display this help message");
  print_status ("-V - Display version number and exit");
}


static void process_cmd_line(state *s, int argc, char **argv)
{
  int i, match_files_loaded = FALSE;

  while ((i=getopt(argc,argv,"gavhVpdsblcxt:rm:k:")) != -1) {
    switch(i) {
      
    case 'g':
      s->mode |= mode_cluster;
      break;

    case 'a':
      s->mode |= mode_display_all;
      break;

    case 'v': 
      if (MODE(mode_verbose))
      {
	print_error(s,"%s: Already at maximum verbosity", __progname);
	print_error(s,
		    "%s: Error message displayed to user correctly", 
		    __progname);
      }
      else
	s->mode |= mode_verbose;
      break;
      
    case 'p':
      s->mode |= mode_match_pretty;
      break;

    case 'd':
      s->mode |= mode_directory; 
      break;

    case 's':
      s->mode |= mode_silent; break;

    case 'b':
      s->mode |= mode_barename; break;

    case 'l':
      s->mode |= mode_relative; break;

    case 'c':
      s->mode |= mode_csv; break;

    case 'x':
      s->mode |= mode_sigcompare; break;

    case 'r':
      s->mode |= mode_recursive; break;

    case 't':
      s->threshold = (uint8_t)atol(optarg);
      if (s->threshold > 100)
	fatal_error("%s: Illegal threshold", __progname);
      s->mode |= mode_threshold;
      break;
      
    case 'm':
      if (MODE(mode_compare_unknown) || MODE(mode_sigcompare))
	fatal_error("Positive matching cannot be combined with other matching modes");
      s->mode |= mode_match;
      if (not match_load(s,optarg))
	match_files_loaded = TRUE;
      break;
      
    case 'k':
      if (MODE(mode_match) || MODE(mode_sigcompare))
	fatal_error("Signature matching cannot be combined with other matching modes");
      s->mode |= mode_compare_unknown;
      if (not match_load(s,optarg))
	match_files_loaded = TRUE;
      break;

    case 'h':
      usage(); 
      exit (EXIT_SUCCESS);
      
    case 'V':
      print_status ("%s", VERSION);
      exit (EXIT_SUCCESS);
      
    default:
      try_msg();
      exit (EXIT_FAILURE);
    }
  }

  // We don't include mode_sigcompare in this list as we haven't loaded
  // the matching files yet. In that mode the matching files are in fact 
  // the command line arguments.
  sanity_check(s,
	       ((MODE(mode_match) || MODE(mode_compare_unknown))
		&& not match_files_loaded),
	       "No matching files loaded");
  
  sanity_check(s,
	       ((s->mode & mode_barename) && (s->mode & mode_relative)),
	       "Relative paths and bare names are mutually exclusive");

  sanity_check(s,
	       ((s->mode & mode_match_pretty) && (s->mode & mode_directory)),
	       "Directory mode and pretty matching are mutually exclusive");

  sanity_check(s,
	       MODE(mode_csv) and MODE(mode_cluster),
	       "CSV and clustering modes cannot be combined");

  // -m, -p, and -d are incompatible with -k and -x
  // The former treat FILES as raw files. The latter require them to be sigs
  sanity_check(s,
	       ((MODE(mode_match) or MODE(mode_match_pretty) or MODE(mode_directory))
		and
		(MODE(mode_compare_unknown) or MODE(mode_sigcompare))),
	       "Incompatible matching modes");


}





#ifdef _WIN32
static int prepare_windows_command_line(state *s)
{
  int argc;
  TCHAR **argv;

  argv = CommandLineToArgvW(GetCommandLineW(),&argc);
  
  s->argc = argc;
  s->argv = argv;

  return FALSE;
}
#endif


static int is_absolute_path(TCHAR *fn)
{
  if (NULL == fn)
    internal_error("Unknown error in is_absolute_path");
  
#ifdef _WIN32
  return (isalpha(fn[0]) and _TEXT(':') == fn[1]);
# else
  return (DIR_SEPARATOR == fn[0]);
#endif
}


static void generate_filename(state *s, TCHAR *fn, TCHAR *cwd, TCHAR *input)
{
  if (NULL == fn || NULL == input)
    internal_error("Error calling generate_filename");

  if ((s->mode & mode_relative) || is_absolute_path(input))
    _tcsncpy(fn, input, SSDEEP_PATH_MAX);
  else {
    // Windows systems don't have symbolic links, so we don't
    // have to worry about carefully preserving the paths
    // they follow. Just use the system command to resolve the paths
#ifdef _WIN32
    _wfullpath(fn, input, SSDEEP_PATH_MAX);
#else     
    if (NULL == cwd)
      // If we can't get the current working directory, we're not
      // going to be able to build the relative path to this file anyway.
      // So we just call realpath and make the best of things
      realpath(input, fn);
    else
      snprintf(fn, SSDEEP_PATH_MAX, "%s%c%s", cwd, DIR_SEPARATOR, input);
#endif
  }
}


int main(int argc, char **argv)
{
  int count, status, goal = argc;
  state *s;
  TCHAR *fn, *cwd;

#ifndef __GLIBC__
  //  __progname  = basename(argv[0]);
#endif
  
  s = new state;
  if (initialize_state(s))
    fatal_error("%s: Unable to initialize state variable", __progname);

  process_cmd_line(s,argc,argv);

#ifdef _WIN32
  if (prepare_windows_command_line(s))
    fatal_error("%s: Unable to process command line arguments", __progname);
#else
  s->argc = argc;
  s->argv = argv;
#endif

  // Anything left on the command line at this point is a file
  // or directory we're supposed to process. If there's nothing
  // specified, we should tackle standard input 
  if (optind == argc) {
    status = process_stdin(s);
  }
  else {
    MD5DEEP_ALLOC(TCHAR, fn, SSDEEP_PATH_MAX);
    MD5DEEP_ALLOC(TCHAR, cwd, SSDEEP_PATH_MAX);
    
    cwd = _tgetcwd(cwd, SSDEEP_PATH_MAX);
    if (NULL == cwd)
      fatal_error("%s: %s", __progname, strerror(errno));
  
    count = optind;
  
    // The signature comparsion mode needs to use the command line
    // arguments and argument count. We don't do wildcard expansion
    // on it on Win32 (i.e. where it matters). The setting of 'goal'
    // to the original argc occured at the start of main(), so we just
    // need to update it if we're *not* in signature compare mode.
    if (not (s->mode & mode_sigcompare)) {
      goal = s->argc;
    }
    
    while (count < goal)
    {
      if (MODE(mode_sigcompare))
	match_load(s,argv[count]);
      else if (MODE(mode_compare_unknown))
	match_compare_unknown(s,argv[count]);
      else {
	generate_filename(s, fn, cwd, s->argv[count]);
	
#ifdef _WIN32
	status = process_win32(s, fn);
#else
	status = process_normal(s, fn);
#endif
      }
      
      ++count;
    }

    // If we processed files, but didn't find anything large enough
    // to be meaningful, we should display a warning message to the user.
    // This happens mostly when people are testing very small files
    // e.g. $ echo "hello world" > foo && ssdeep foo
    if ((not s->found_meaningful_file) and s->processed_file)
    {
      print_error(s,"%s: Did not process files large enough to produce meaningful results", __progname);
    }
  }


  // If the user has requested us to compare signature files, use
  // our existng code to pretty-print directory matching to do the
  // work for us.
  if (MODE(mode_sigcompare))
    s->mode |= mode_match_pretty;
  if (MODE(mode_match_pretty) or MODE(mode_sigcompare) or MODE(mode_cluster))
    find_matches_in_known(s);
  if (MODE(mode_cluster))
    display_clusters(s);

  return (EXIT_SUCCESS);
}
