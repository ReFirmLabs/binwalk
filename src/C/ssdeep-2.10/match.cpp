// ssdeep
// (C) Copyright 2012 Kyrus
//
// $Id: match.cpp 164 2012-07-23 16:12:36Z jessekornblum $
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
//You should have received a copy of the GNU General Public License
// along with this program; if not, write to the Free Software
// Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA


#include "match.h"

// The longest line we should encounter when reading files of known hashes 
#define MAX_STR_LEN  2048

#define MIN_SUBSTR_LEN 7

// ------------------------------------------------------------------
// SIGNATURE FILE FUNCTIONS
// ------------------------------------------------------------------

/// Open a file of known hashes and determine if it's valid
///
/// @param s State variable
/// @param fn filename to open
/// 
/// @return Returns false success, true on error
bool sig_file_open(state *s, const char * fn)
{
  if (NULL == s or NULL == fn)
    return true;

  s->known_handle = fopen(fn,"rb");
  if (NULL == s->known_handle)
  {
    if ( ! (MODE(mode_silent)) )
      perror(fn);
    return true;
  }

  // The first line of the file should contain a valid ssdeep header. 
  char buffer[MAX_STR_LEN];
  if (NULL == fgets(buffer,MAX_STR_LEN,s->known_handle))
  {
    if ( ! (MODE(mode_silent)) )
      perror(fn);
    fclose(s->known_handle);
    return true;
  }

  chop_line(buffer);

  if (strncmp(buffer,SSDEEPV1_0_HEADER,MAX_STR_LEN) and 
      strncmp(buffer,SSDEEPV1_1_HEADER,MAX_STR_LEN)) 
  {
    if ( ! (MODE(mode_silent)) )
      print_error(s,"%s: Invalid file header.", fn);
    fclose(s->known_handle);
    return true;
  }

  // We've now read the first line
  s->line_number = 1;
  s->known_fn = strdup(fn);

  return false;
}



/// @brief Read the next entry in a file of known hashes and convert 
/// it to a Filedata 
///
/// @param s State variable
/// @param f Structure where to store the data we read
///
/// @return Returns true if there is no entry to read or on error. 
/// Otherwise, false.
bool sig_file_next(state *s, Filedata ** f)
{
  if (NULL == s or NULL == f or NULL == s->known_handle)
    return true;

  char buffer[MAX_STR_LEN];
  memset(buffer,0,MAX_STR_LEN);
  if (NULL == fgets(buffer,MAX_STR_LEN,s->known_handle))
    return true;

  s->line_number++;
  chop_line(buffer);

  try 
  {
    *f = new Filedata(std::string(buffer),s->known_fn);
  }
  catch (std::bad_alloc)
  {
    // This can happen on a badly formatted line, or a blank one.
    // We don't display errors on blank lines.
    if (strlen(buffer) > 0)
      print_error(s,
		  "%s: Bad hash in line %llu", 
		  s->known_fn, 
		  s->line_number);

    return true;
  }

  return false;
}


bool sig_file_close(state *s)
{
  if (NULL == s)
    return true;

  free(s->known_fn);

  if (s->known_handle != NULL) 
    return true;

  if (fclose(s->known_handle))
    return true;
  
  return false;
}


bool sig_file_end(state *s)
{
  return (feof(s->known_handle));
}



// ------------------------------------------------------------------
// MATCHING FUNCTIONS
// ------------------------------------------------------------------

void display_clusters(const state *s)
{
  if (NULL == s)
    return;

  std::set<std::set<Filedata *> *>::const_iterator it;
  for (it = s->all_clusters.begin(); it != s->all_clusters.end() ; ++it)
  {
    print_status("** Cluster size %u", (*it)->size());
    std::set<Filedata *>::const_iterator cit;
    for (cit = (*it)->begin() ; cit != (*it)->end() ; ++cit)
    {
      display_filename(stdout,(*cit)->get_filename(),FALSE);
      print_status("");
    }
    
    print_status("");
  }
}


void cluster_add(Filedata * dest, Filedata * src)
{
  dest->get_cluster()->insert(src);
  src->set_cluster(dest->get_cluster());
}


void cluster_join(state *s, Filedata * a, Filedata * b)
{
  // If these items are already in the same cluster there is nothing to do
  if (a->get_cluster() == b->get_cluster())
    return;

  Filedata * dest, * src;
  // Combine the smaller cluster into the larger cluster for speed
  // (fewer items to move)
  if (a->get_cluster()->size() > b->get_cluster()->size())
  {
    dest = a; 
    src  = b;
  }
  else
  {
    dest = b; 
    src  = a;
  }

  // Add members of src to dest
  std::set<Filedata *>::const_iterator it;
  for (it =  src->get_cluster()->begin() ; 
       it != src->get_cluster()->end() ; 
       ++it)
  {
    dest->get_cluster()->insert(*it);
  }

  // Remove the old cluster
  s->all_clusters.erase(src->get_cluster());
  // This call sets the cluster to NULL. Do not access the src
  // cluster after this call!
  src->clear_cluster();

  src->set_cluster(dest->get_cluster());
}


void handle_clustering(state *s, Filedata *a, Filedata *b)
{
  bool a_has = a->has_cluster(), b_has = b->has_cluster();

  // In the easiest case, one of these has a cluster and one doesn't
  if (a_has and not b_has)
  {
    cluster_add(a,b);
    return;
  }
  if (b_has and not a_has)
  {
    cluster_add(b,a);
    return;
  }
  
  // Combine existing clusters
  if (a_has and b_has)
  {
    cluster_join(s,a,b);
    return;
  }

  // Create a new cluster
  std::set<Filedata *> * cluster = new std::set<Filedata *>();
  cluster->insert(a);
  cluster->insert(b);

  s->all_clusters.insert(cluster);

  a->set_cluster(cluster);
  b->set_cluster(cluster);
}



void handle_match(state *s, 
		  Filedata *a, 
		  Filedata *b, 
		  int score)
{
  if (s->mode & mode_csv)
  {
    printf("\"");
    display_filename(stdout,a->get_filename(),TRUE);
    printf("\",\"");
    display_filename(stdout,b->get_filename(),TRUE);
    print_status("\",%u", score);
  }
  else if (s->mode & mode_cluster)
  {
    handle_clustering(s,a,b);
  }
  else
  {
    // The match file names may be empty. If so, we don't print them
    // or the colon which separates them from the filename
    if (a->has_match_file())
      printf ("%s:", a->get_match_file().c_str());
    display_filename(stdout,a->get_filename(),FALSE);
    printf (" matches ");
    if (b->has_match_file())
      printf ("%s:", b->get_match_file().c_str());
    display_filename(stdout,b->get_filename(),FALSE);
    print_status(" (%u)", score);
  }
}


bool match_compare(state *s, Filedata * f)
{
  if (NULL == s)
    fatal_error("%s: Null state passed into match_compare", __progname);

  bool status = false;  
  size_t fn_len = _tcslen(f->get_filename());

  std::vector<Filedata* >::const_iterator it;
  for (it = s->all_files.begin() ; it != s->all_files.end() ; ++it)
  {
    // When in pretty mode, we still want to avoid printing
    // A matches A (100).
    if (s->mode & mode_match_pretty)
    {
      if (!(_tcsncmp(f->get_filename(),
		     (*it)->get_filename(),
		     std::max(fn_len,_tcslen((*it)->get_filename())))) and
	  (f->get_signature() == (*it)->get_signature()))
      {
	// Unless these results from different matching files (such as
	// what happens in sigcompare mode). That being said, we have to
	// be careful to avoid NULL values such as when working in 
	// normal pretty print mode.
	if (not(f->has_match_file()) or 
	    f->get_match_file() == (*it)->get_match_file())
	  continue;
      }
    }

    int score =  fuzzy_compare(f->get_signature().c_str(), 
			       (*it)->get_signature().c_str());
    if (-1 == score)
      print_error(s, "%s: Bad hashes in comparison", __progname);
    else
    {
      if (score > s->threshold or MODE(mode_display_all))
      {
	handle_match(s,f,(*it),score);
	status = true;
      }
    }
  }
  
  return status;
}
  

bool find_matches_in_known(state *s)
{
  if (NULL == s)
    return true;

  // Walk the vector which contains all of the known files
  std::vector<Filedata *>::const_iterator it;
  for (it = s->all_files.begin() ; it != s->all_files.end() ; ++it)
  {
    bool status = match_compare(s,*it);
    // In pretty mode and sigcompare mode we need to display a blank
    // line after each file. In clustering mode we don't display anything
    // right now.
    if (status and not(MODE(mode_cluster)))
      print_status("");
  }

  return false;
}


bool match_add(state *s, Filedata * f)
{
  if (NULL == s)
    return true;

  s->all_files.push_back(f);

  return false;
}


bool match_load(state *s, const char *fn)
{
  if (NULL == s or NULL == fn)
    return true;

  if (sig_file_open(s,fn))
    return true;

  bool status;

  do 
  {
    Filedata * f; 
    status = sig_file_next(s,&f);
    if (not status)
    {
      if (match_add(s,f))
      {
	// One bad hash doesn't mean this load was a failure.
	// We don't change the return status because match_add failed.
	print_error(s,"%s: unable to insert hash", fn);
	break;
      }
    }
  } while (not sig_file_end(s));

  sig_file_close(s);

  return false;
}


bool match_compare_unknown(state *s, const char * fn)
{ 
  if (NULL == s or NULL == fn)
    return true;

  if (sig_file_open(s,fn))
    return true;

  bool status;
  
  do
  {
    Filedata *f;
    status = sig_file_next(s,&f);
    if (not status)
      match_compare(s,f);
  } while (not sig_file_end(s));

  sig_file_close(s);

  return false;
}

