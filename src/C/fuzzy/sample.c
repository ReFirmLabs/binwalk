/* Fuzzy Hashing by Jesse Kornblum
   Copyright (C) 2010 ManTech International Corporation

   This program demonstrates some of the capabilities of 
   the fuzzy hashing library.
   
   To compile the program using gcc:

   $ gcc -Wall -I/usr/local/include -L/usr/local/lib sample.c -Lfuzzy

   Using mingw:

   C:\> gcc -Wall -Ic:\path\to\includes sample.c fuzzy.dll

   Using Microsoft Visual C:

   C:\> lib /machine:i386 /def:fuzzy.def
   C:\> cl sample.c fuzzy.lib

   See the README that came with this file for more details on using
   the library on Windows systems with Microsoft Visual C. 


   The functions generate_random and write_data are generic routines to make
   random data for hashing. The real magic happens in the main() function.

   THIS SOFTWARE IS NOT DESIGNED OR INTENDED FOR USE OR RESALE AS ON-LINE
   CONTROL EQUIPMENT IN HAZARDOUS ENVIRONMENTS REQUIRING FAIL-SAFE
   PERFORMANCE, SUCH AS IN THE OPERATION OF NUCLEAR FACILITIES, AIRCRAFT
   NAVIGATION OR COMMUNICATION SYSTEMS, AIR TRAFFIC CONTROL, DIRECT LIFE
   SUPPORT MACHINES, OR WEAPONS SYSTEMS, IN WHICH THE FAILURE OF THE
   SOFTWARE COULD LEAD DIRECTLY TO DEATH, PERSONAL INJURY, OR SEVERE
   PHYSICAL OR ENVIRONMENTAL DAMAGE ("HIGH RISK ACTIVITIES").  THE AUTHOR
   SPECIFICALLY DISCLAIMS ANY EXPRESS OR IMPLIED WARRANTY OF FITNESS FOR
   HIGH RISK ACTIVITIES.   */

// $Id: sample.c 97 2010-03-19 15:10:06Z jessekornblum $

#include <stdio.h>
#include <stdlib.h>
#include <inttypes.h>

#include <fuzzy.h>

#define FILENAME "foo.dat" 
#define SIZE 0x50000


void generate_random(unsigned char *buf, uint32_t sz)
{
  uint32_t i;

  for (i = 0 ; i < sz ; ++i)
    buf[i] = (unsigned char)(rand() % 255);
  buf[(sz-1)] = 0;
}


int write_data(const unsigned char *buf, 
	       const uint32_t sz, 
	       const char *fn)
{
  printf ("Writing to %s\n", fn);
  FILE * handle = fopen(fn,"wb");
  if (NULL == handle)
    return 1;
  fwrite(buf,sz,1,handle);
  fclose(handle);
  
  return 0;
}


int main(int argc, char **argv)
{
  unsigned char * buf;
  char * result, * result2;
  FILE *handle; 

  srand(1);

  buf     = (unsigned char *)malloc(SIZE);
  result  = (char *)malloc(FUZZY_MAX_RESULT);
  result2 = (char *)malloc(FUZZY_MAX_RESULT);
  if (NULL == result || NULL == buf || NULL == result2)
  {
    fprintf (stderr,"%s: Out of memory\n", argv[0]);
    return EXIT_FAILURE;
  }

  generate_random(buf,SIZE);

  if (write_data(buf,SIZE,FILENAME))
    return EXIT_FAILURE;

  printf ("Hashing buffer\n");
  int status = fuzzy_hash_buf(buf,SIZE,result);
  if (status)
    printf ("Error during buf hash\n");
  else
    printf ("%s\n", result);
 
  handle = fopen(FILENAME,"rb");
  if (NULL == handle)
    {
      perror(FILENAME);
      return EXIT_FAILURE;
    }

  printf ("Hashing file\n");
  status = fuzzy_hash_file(handle,result);
  if (status)
    printf ("Error during file hash\n");
  else
    printf ("%s\n", result);
  fclose(handle);


  printf ("Modifying buffer and comparing to file\n");
  int i;
  for (i = 0x100 ; i < 0x110 ; ++i)
    buf[i] = 37;
  status = fuzzy_hash_buf(buf,SIZE,result2);  
  if (status)
    printf ("Error during buffer hash\n");
  else
    printf ("%s\n", result2);

  i = fuzzy_compare(result,result2);
  if (-1 == i)
    printf ("An error occured during matching\n");
  else
  {
    if (i != 0)
      printf ("MATCH: score = %d\n", i);
    else
      printf ("did not match\n");
  }

  return EXIT_SUCCESS;
}
