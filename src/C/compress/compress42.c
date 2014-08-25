/* (N)compress42.c - File compression ala IEEE Computer, Mar 1992.
 *
 * Authors:
 *   Spencer W. Thomas   (decvax!harpo!utah-cs!utah-gr!thomas)
 *   Jim McKie           (decvax!mcvax!jim)
 *   Steve Davies        (decvax!vax135!petsd!peora!srd)
 *   Ken Turkowski       (decvax!decwrl!turtlevax!ken)
 *   James A. Woods      (decvax!ihnp4!ames!jaw)
 *   Joe Orost           (decvax!vax135!petsd!joe)
 *   Dave Mack           (csu@alembic.acs.com)
 *   Peter Jannesen, Network Communication Systems
 *                       (peter@ncs.nl)
 *
 * Revision 4.2.3  92/03/14 peter@ncs.nl
 *   Optimise compress and decompress function and a lot of cleanups.
 *   New fast hash algoritme added (if more than 800Kb available).
 *
 * Revision 4.1  91/05/26 csu@alembic.acs.com
 *   Modified to recursively compress directories ('r' flag). As a side
 *   effect, compress will no longer attempt to compress things that
 *   aren't "regular" files. See Changes.
 *
 * Revision 4.0  85/07/30  12:50:00  joe
 *   Removed ferror() calls in output routine on every output except first.
 *   Prepared for release to the world.
 * 
 * Revision 3.6  85/07/04  01:22:21  joe
 *   Remove much wasted storage by overlaying hash table with the tables
 *   used by decompress: tab_suffix[1<<BITS], stack[8000].  Updated USERMEM
 *   computations.  Fixed dump_tab() DEBUG routine.
 *
 * Revision 3.5  85/06/30  20:47:21  jaw
 *   Change hash function to use exclusive-or.  Rip out hash cache.  These
 *   speedups render the megamemory version defunct, for now.  Make decoder
 *   stack global.  Parts of the RCS trunks 2.7, 2.6, and 2.1 no longer apply.
 *
 * Revision 3.4  85/06/27  12:00:00  ken
 *   Get rid of all floating-point calculations by doing all compression ratio
 *   calculations in fixed point.
 *
 * Revision 3.3  85/06/24  21:53:24  joe
 *   Incorporate portability suggestion for M_XENIX.  Got rid of text on #else
 *   and #endif lines.  Cleaned up #ifdefs for vax and interdata.
 *
 * Revision 3.2  85/06/06  21:53:24  jaw
 *   Incorporate portability suggestions for Z8000, IBM PC/XT from mailing list.
 *   Default to "quiet" output (no compression statistics).
 *
 * Revision 3.1  85/05/12  18:56:13  jaw
 *   Integrate decompress() stack speedups (from early pointer mods by McKie).
 *   Repair multi-file USERMEM gaffe.  Unify 'force' flags to mimic semantics
 *   of SVR2 'pack'.  Streamline block-compress table clear logic.  Increase 
 *   output byte count by magic number size.
 * 
 * Revision 3.0   84/11/27  11:50:00  petsd!joe
 *   Set HSIZE depending on BITS.  Set BITS depending on USERMEM.  Unrolled
 *   loops in clear routines.  Added "-C" flag for 2.0 compatibility.  Used
 *   unsigned compares on Perkin-Elmer.  Fixed foreground check.
 *
 * Revision 2.7   84/11/16  19:35:39  ames!jaw
 *   Cache common hash codes based on input statistics; this improves
 *   performance for low-density raster images.  Pass on #ifdef bundle
 *   from Turkowski.
 *
 * Revision 2.6   84/11/05  19:18:21  ames!jaw
 *   Vary size of hash tables to reduce time for small files.
 *   Tune PDP-11 hash function.
 *
 * Revision 2.5   84/10/30  20:15:14  ames!jaw
 *   Junk chaining; replace with the simpler (and, on the VAX, faster)
 *   double hashing, discussed within.  Make block compression standard.
 *
 * Revision 2.4   84/10/16  11:11:11  ames!jaw
 *   Introduce adaptive reset for block compression, to boost the rate
 *   another several percent.  (See mailing list notes.)
 *
 * Revision 2.3   84/09/22  22:00:00  petsd!joe
 *   Implemented "-B" block compress.  Implemented REVERSE sorting of tab_next.
 *   Bug fix for last bits.  Changed fwrite to putchar loop everywhere.
 *
 * Revision 2.2   84/09/18  14:12:21  ames!jaw
 *   Fold in news changes, small machine typedef from thomas,
 *   #ifdef interdata from joe.
 *
 * Revision 2.1   84/09/10  12:34:56  ames!jaw
 *   Configured fast table lookup for 32-bit machines.
 *   This cuts user time in half for b <= FBITS, and is useful for news batching
 *   from VAX to PDP sites.  Also sped up decompress() [fwrite->putc] and
 *   added signal catcher [plus beef in write_error()] to delete effluvia.
 *
 * Revision 2.0   84/08/28  22:00:00  petsd!joe
 *   Add check for foreground before prompting user.  Insert maxbits into
 *   compressed file.  Force file being uncompressed to end with ".Z".
 *   Added "-c" flag and "zcat".  Prepared for release.
 *
 * Revision 1.10  84/08/24  18:28:00  turtlevax!ken
 *   Will only compress regular files (no directories), added a magic number
 *   header (plus an undocumented -n flag to handle old files without headers),
 *   added -f flag to force overwriting of possibly existing destination file,
 *   otherwise the user is prompted for a response.  Will tack on a .Z to a
 *   filename if it doesn't have one when decompressing.  Will only replace
 *   file if it was compressed.
 *
 * Revision 1.9  84/08/16  17:28:00  turtlevax!ken
 *   Removed scanargs(), getopt(), added .Z extension and unlimited number of
 *   filenames to compress.  Flags may be clustered (-Ddvb12) or separated
 *   (-D -d -v -b 12), or combination thereof.  Modes and other status is
 *   copied with copystat().  -O bug for 4.2 seems to have disappeared with
 *   1.8.
 *
 * Revision 1.8  84/08/09  23:15:00  joe
 *   Made it compatible with vax version, installed jim's fixes/enhancements
 *
 * Revision 1.6  84/08/01  22:08:00  joe
 *   Sped up algorithm significantly by sorting the compress chain.
 *
 * Revision 1.5  84/07/13  13:11:00  srd
 *   Added C version of vax asm routines.  Changed structure to arrays to
 *   save much memory.  Do unsigned compares where possible (faster on
 *   Perkin-Elmer)
 *
 * Revision 1.4  84/07/05  03:11:11  thomas
 *   Clean up the code a little and lint it.  (Lint complains about all
 *   the regs used in the asm, but I'm not going to "fix" this.)
 *
 * Revision 1.3  84/07/05  02:06:54  thomas
 *   Minor fixes.
 *
 * Revision 1.2  84/07/05  00:27:27  thomas
 *   Add variable bit length output.
 *
 */
#include	<stdio.h>
#include	<stdlib.h>
#include	<string.h>
#include	<unistd.h>
#include	<fcntl.h>
#include	<ctype.h>
#include	<signal.h>
#include	<sys/types.h>
#include	<sys/stat.h>
#include	<errno.h>

#ifdef DIRENT
#	include	<dirent.h>
#	define	RECURSIVE		1
#	undef	SYSDIR
#endif
#ifdef SYSDIR
#	include	<sys/dir.h>
#	define	RECURSIVE		1
#endif
#ifdef UTIME_H
#	include	<utime.h>
#else
	struct utimbuf {
		time_t actime;
		time_t modtime;
	};
#endif

#ifdef	__STDC__
#	define	ARGS(a)				a
#else
#	define	ARGS(a)				()
#endif

#define	LARGS(a)	()	/* Relay on include files for libary func defs. */

#ifndef SIG_TYPE
#	define	SIG_TYPE	void (*)()
#endif

/* CJH */
#define NOFUNCDEF
#ifndef NOFUNCDEF
	extern	void	*malloc	LARGS((int));
	extern	void	free	LARGS((void *));
#ifndef _IBMR2
	extern	int		open	LARGS((char const *,int,...));
#endif
	extern	int		close	LARGS((int));
	extern	int		read	LARGS((int,void *,int));
	extern	int		write	LARGS((int,void const *,int));
	extern	int		chmod	LARGS((char const *,int));
	extern	int		unlink	LARGS((char const *));
	extern	int		chown	LARGS((char const *,int,int));
	extern	int		utime	LARGS((char const *,struct utimbuf const *));
	extern	char	*strcpy	LARGS((char *,char const *));
	extern	char	*strcat	LARGS((char *,char const *));
	extern	int		strcmp	LARGS((char const *,char const *));
	extern	unsigned strlen	LARGS((char const *));
	extern	void	*memset	LARGS((void *,char,unsigned int));
	extern	void	*memcpy	LARGS((void *,void const *,unsigned int));
	extern	int		atoi	LARGS((char const *));
	extern	int		isatty	LARGS((int));
#endif
	
#define	MARK(a)	{ asm(" .globl M.a"); asm("M.a:"); }

#ifdef	DEF_ERRNO
	extern int	errno;
#endif

/* CJH */
//#include "patchlevel.h"

#undef	min
#define	min(a,b)	((a>b) ? b : a)

#ifndef	IBUFSIZ
#	define	IBUFSIZ	BUFSIZ	/* Defailt input buffer size							*/
#endif
#ifndef	OBUFSIZ
#	define	OBUFSIZ	BUFSIZ	/* Default output buffer size							*/
#endif

#define MAXPATHLEN 1024		/* MAXPATHLEN - maximum length of a pathname we allow 	*/
#define	SIZE_INNER_LOOP		256	/* Size of the inter (fast) compress loop			*/

							/* Defines for third byte of header 					*/
#define	MAGIC_1		(char_type)'\037'/* First byte of compressed file				*/
#define	MAGIC_2		(char_type)'\235'/* Second byte of compressed file				*/
#define BIT_MASK	0x1f			/* Mask for 'number of compresssion bits'		*/
									/* Masks 0x20 and 0x40 are free.  				*/
									/* I think 0x20 should mean that there is		*/
									/* a fourth header byte (for expansion).    	*/
#define BLOCK_MODE	0x80			/* Block compresssion if table is full and		*/
									/* compression rate is dropping flush tables	*/

			/* the next two codes should not be changed lightly, as they must not	*/
			/* lie within the contiguous general code space.						*/
#define FIRST	257					/* first free entry 							*/
#define	CLEAR	256					/* table clear output code 						*/

#define INIT_BITS 9			/* initial number of bits/code */

#ifndef SACREDMEM
	/*
 	 * SACREDMEM is the amount of physical memory saved for others; compress
 	 * will hog the rest.
 	 */
#	define SACREDMEM	0
#endif

#ifndef USERMEM
	/*
 	 * Set USERMEM to the maximum amount of physical user memory available
 	 * in bytes.  USERMEM is used to determine the maximum BITS that can be used
 	 * for compression.
	 */
#	define USERMEM 	450000	/* default user memory */
#endif

#ifndef	BYTEORDER
#	define	BYTEORDER	0000
#endif

#ifndef	NOALLIGN
#	define	NOALLIGN	0
#endif

/*
 * machine variants which require cc -Dmachine:  pdp11, z8000, DOS
 */

#ifdef interdata	/* Perkin-Elmer													*/
#	define SIGNED_COMPARE_SLOW	/* signed compare is slower than unsigned 			*/
#endif

#ifdef pdp11	 	/* PDP11: don't forget to compile with -i 						*/
#	define	BITS 		12	/* max bits/code for 16-bit machine 					*/
#	define	NO_UCHAR		/* also if "unsigned char" functions as signed char 	*/
#endif /* pdp11 */

#ifdef z8000		/* Z8000: 														*/
#	define	BITS 	12	/* 16-bits processor max 12 bits							*/
#	undef	vax			/* weird preprocessor 										*/
#endif /* z8000 */

#ifdef	DOS			/* PC/XT/AT (8088) processor									*/
#	define	BITS   16	/* 16-bits processor max 12 bits							*/
#	if BITS == 16
#		define	MAXSEG_64K
#	endif
#	undef	BYTEORDER
#	define	BYTEORDER 	4321
#	undef	NOALLIGN
#	define	NOALLIGN	1
#	define	COMPILE_DATE	__DATE__
#endif /* DOS */

#ifndef	O_BINARY
#	define	O_BINARY	0	/* System has no binary mode							*/
#endif

#ifdef M_XENIX			/* Stupid compiler can't handle arrays with */
#	if BITS == 16 		/* more than 65535 bytes - so we fake it */
# 		define MAXSEG_64K
#	else
#	if BITS > 13			/* Code only handles BITS = 12, 13, or 16 */
#		define BITS	13
#	endif
#	endif
#endif

#ifndef BITS		/* General processor calculate BITS								*/
#	if USERMEM >= (800000+SACREDMEM)
#		define FAST
#	else
#	if USERMEM >= (433484+SACREDMEM)
#		define BITS	16
#	else
#	if USERMEM >= (229600+SACREDMEM)
#		define BITS	15
#	else
#	if USERMEM >= (127536+SACREDMEM)
#		define BITS	14
#   else
#	if USERMEM >= (73464+SACREDMEM)
#		define BITS	13
#	else
#		define BITS	12
#	endif
#	endif
#   endif
#	endif
#	endif
#endif /* BITS */

#ifdef FAST
#	define	HBITS		17			/* 50% occupancy */
#	define	HSIZE	   (1<<HBITS)
#	define	HMASK	   (HSIZE-1)
#	define	HPRIME		 9941
#	define	BITS		   16
#	undef	MAXSEG_64K
#else
#	if BITS == 16
#		define HSIZE	69001		/* 95% occupancy */
#	endif
#	if BITS == 15
#		define HSIZE	35023		/* 94% occupancy */
#	endif
#	if BITS == 14
#		define HSIZE	18013		/* 91% occupancy */
#	endif
#	if BITS == 13
#		define HSIZE	9001		/* 91% occupancy */
#	endif
#	if BITS <= 12
#		define HSIZE	5003		/* 80% occupancy */
#	endif
#endif

#define CHECK_GAP 10000

typedef long int			code_int;

#ifdef SIGNED_COMPARE_SLOW
	typedef unsigned long int	count_int;
	typedef unsigned short int	count_short;
	typedef unsigned long int	cmp_code_int;	/* Cast to make compare faster	*/
#else
	typedef long int	 		count_int;
	typedef long int			cmp_code_int;
#endif

typedef	unsigned char	char_type;

#define ARGVAL() (*++(*argv) || (--argc && *++argv))

#define MAXCODE(n)	(1L << (n))

#ifndef	REGISTERS
#	define	REGISTERS	2
#endif
#define	REG1	
#define	REG2	
#define	REG3	
#define	REG4	
#define	REG5	
#define	REG6	
#define	REG7	
#define	REG8	
#define	REG9	
#define	REG10
#define	REG11	
#define	REG12	
#define	REG13
#define	REG14
#define	REG15
#define	REG16
#if REGISTERS >= 1
#	undef	REG1
#	define	REG1	register
#endif
#if REGISTERS >= 2
#	undef	REG2
#	define	REG2	register
#endif
#if REGISTERS >= 3
#	undef	REG3
#	define	REG3	register
#endif
#if REGISTERS >= 4
#	undef	REG4
#	define	REG4	register
#endif
#if REGISTERS >= 5
#	undef	REG5
#	define	REG5	register
#endif
#if REGISTERS >= 6
#	undef	REG6
#	define	REG6	register
#endif
#if REGISTERS >= 7
#	undef	REG7
#	define	REG7	register
#endif
#if REGISTERS >= 8
#	undef	REG8
#	define	REG8	register
#endif
#if REGISTERS >= 9
#	undef	REG9
#	define	REG9	register
#endif
#if REGISTERS >= 10
#	undef	REG10
#	define	REG10	register
#endif
#if REGISTERS >= 11
#	undef	REG11
#	define	REG11	register
#endif
#if REGISTERS >= 12
#	undef	REG12
#	define	REG12	register
#endif
#if REGISTERS >= 13
#	undef	REG13
#	define	REG13	register
#endif
#if REGISTERS >= 14
#	undef	REG14
#	define	REG14	register
#endif
#if REGISTERS >= 15
#	undef	REG15
#	define	REG15	register
#endif
#if REGISTERS >= 16
#	undef	REG16
#	define	REG16	register
#endif


union	bytes
{
	long	word;
	struct
	{
#if BYTEORDER == 4321
		char_type	b1;
		char_type	b2;
		char_type	b3;
		char_type	b4;
#else
#if BYTEORDER == 1234
		char_type	b4;
		char_type	b3;
		char_type	b2;
		char_type	b1;
#else
#	undef	BYTEORDER
		int				dummy;
#endif
#endif
	} bytes;
} ;
#if BYTEORDER == 4321 && NOALLIGN == 1
#define	output(b,o,c,n)	{													\
							*(long *)&((b)[(o)>>3]) |= ((long)(c))<<((o)&0x7);\
							(o) += (n);										\
						}
#else
#ifdef BYTEORDER
#define	output(b,o,c,n)	{	REG1 char_type	*p = &(b)[(o)>>3];				\
							union bytes i;									\
							i.word = ((long)(c))<<((o)&0x7);				\
							p[0] |= i.bytes.b1;								\
							p[1] |= i.bytes.b2;								\
							p[2] |= i.bytes.b3;								\
							(o) += (n);										\
						}
#else
#define	output(b,o,c,n)	{	REG1 char_type	*p = &(b)[(o)>>3];				\
							REG2 long		 i = ((long)(c))<<((o)&0x7);	\
							p[0] |= (char_type)(i);							\
							p[1] |= (char_type)(i>>8);						\
							p[2] |= (char_type)(i>>16);						\
							(o) += (n);										\
						}
#endif
#endif
#if BYTEORDER == 4321 && NOALLIGN == 1
#define	input(b,o,c,n,m){													\
							(c) = (*(long *)(&(b)[(o)>>3])>>((o)&0x7))&(m);	\
							(o) += (n);										\
						}
#else
#define	input(b,o,c,n,m){	REG1 char_type 		*p = &(b)[(o)>>3];			\
							(c) = ((((long)(p[0]))|((long)(p[1])<<8)|		\
									 ((long)(p[2])<<16))>>((o)&0x7))&(m);	\
							(o) += (n);										\
						}
#endif

char			*progname;			/* Program name									*/
int 			silent = 0;			/* don't tell me about errors					*/
int 			quiet = 1;			/* don't tell me about compression 				*/
int				do_decomp = 0;		/* Decompress mode								*/
int				force = 0;			/* Force overwrite of files and links			*/
int				nomagic = 0;		/* Use a 3-byte magic number header,			*/
									/* unless old file 								*/
int				block_mode = BLOCK_MODE;/* Block compress mode -C compatible with 2.0*/
int				maxbits = BITS;		/* user settable max # bits/code 				*/
int 			zcat_flg = 0;		/* Write output on stdout, suppress messages 	*/
int				recursive = 0;  	/* compress directories 						*/
int				exit_code = -1;		/* Exitcode of compress (-1 no file compressed)	*/

char_type		inbuf[IBUFSIZ+64];	/* Input buffer									*/
char_type		outbuf[OBUFSIZ+2048];/* Output buffer								*/

struct stat		infstat;			/* Input file status							*/
char			*ifname;			/* Input filename								*/
int				remove_ofname = 0;	/* Remove output file on a error				*/
char 			ofname[MAXPATHLEN];	/* Output filename								*/
int				fgnd_flag = 0;		/* Running in background (SIGINT=SIGIGN)		*/

long 			bytes_in;			/* Total number of byte from input				*/
long 			bytes_out;			/* Total number of byte to output				*/

/*
 * 8086 & 80286 Has a problem with array bigger than 64K so fake the array
 * For processors with a limited address space and segments.
 */
/*
 * To save much memory, we overlay the table used by compress() with those
 * used by decompress().  The tab_prefix table is the same size and type
 * as the codetab.  The tab_suffix table needs 2**BITS characters.  We
 * get this from the beginning of htab.  The output stack uses the rest
 * of htab, and contains characters.  There is plenty of room for any
 * possible stack (stack used to be 8000 characters).
 */
#ifdef MAXSEG_64K
	count_int htab0[8192];
	count_int htab1[8192];
	count_int htab2[8192];
	count_int htab3[8192];
	count_int htab4[8192];
	count_int htab5[8192];
	count_int htab6[8192];
	count_int htab7[8192];
	count_int htab8[HSIZE-65536];
	count_int * htab[9] = {htab0,htab1,htab2,htab3,htab4,htab5,htab6,htab7,htab8};

	unsigned short code0tab[16384];
	unsigned short code1tab[16384];
	unsigned short code2tab[16384];
	unsigned short code3tab[16384];
	unsigned short code4tab[16384];
	unsigned short * codetab[5] = {code0tab,code1tab,code2tab,code3tab,code4tab};

#	define	htabof(i)			(htab[(i) >> 13][(i) & 0x1fff])
#	define	codetabof(i)		(codetab[(i) >> 14][(i) & 0x3fff])
#	define	tab_prefixof(i)		codetabof(i)
#	define	tab_suffixof(i)		((char_type *)htab[(i)>>15])[(i) & 0x7fff]
#	define	de_stack			((char_type *)(&htab2[8191]))
	void	clear_htab()
	{
		memset(htab0, -1, sizeof(htab0));
		memset(htab1, -1, sizeof(htab1));
		memset(htab2, -1, sizeof(htab2));
		memset(htab3, -1, sizeof(htab3));
		memset(htab4, -1, sizeof(htab4));
		memset(htab5, -1, sizeof(htab5));
		memset(htab6, -1, sizeof(htab6));
		memset(htab7, -1, sizeof(htab7));
		memset(htab8, -1, sizeof(htab8));
	 }
#	define	clear_tab_prefixof()	memset(code0tab, 0, 256);
#else	/* Normal machine */
	count_int		htab[HSIZE];
	unsigned short	codetab[HSIZE];

#	define	htabof(i)				htab[i]
#	define	codetabof(i)			codetab[i]
#	define	tab_prefixof(i)			codetabof(i)
#	define	tab_suffixof(i)			((char_type *)(htab))[i]
#	define	de_stack				((char_type *)&(htab[HSIZE-1]))
#	define	clear_htab()			memset(htab, -1, sizeof(htab))
#	define	clear_tab_prefixof()	memset(codetab, 0, 256);
#endif	/* MAXSEG_64K */

#ifdef FAST
	int primetab[256] =		/* Special secudary hash table.		*/
	{
    	 1013, -1061, 1109, -1181, 1231, -1291, 1361, -1429,
    	 1481, -1531, 1583, -1627, 1699, -1759, 1831, -1889,
    	 1973, -2017, 2083, -2137, 2213, -2273, 2339, -2383,
    	 2441, -2531, 2593, -2663, 2707, -2753, 2819, -2887,
    	 2957, -3023, 3089, -3181, 3251, -3313, 3361, -3449,
    	 3511, -3557, 3617, -3677, 3739, -3821, 3881, -3931,
    	 4013, -4079, 4139, -4219, 4271, -4349, 4423, -4493,
    	 4561, -4639, 4691, -4783, 4831, -4931, 4973, -5023,
    	 5101, -5179, 5261, -5333, 5413, -5471, 5521, -5591,
    	 5659, -5737, 5807, -5857, 5923, -6029, 6089, -6151,
    	 6221, -6287, 6343, -6397, 6491, -6571, 6659, -6709,
    	 6791, -6857, 6917, -6983, 7043, -7129, 7213, -7297,
    	 7369, -7477, 7529, -7577, 7643, -7703, 7789, -7873,
    	 7933, -8017, 8093, -8171, 8237, -8297, 8387, -8461,
    	 8543, -8627, 8689, -8741, 8819, -8867, 8963, -9029,
    	 9109, -9181, 9241, -9323, 9397, -9439, 9511, -9613,
    	 9677, -9743, 9811, -9871, 9941,-10061,10111,-10177,
   		10259,-10321,10399,-10477,10567,-10639,10711,-10789,
   		10867,-10949,11047,-11113,11173,-11261,11329,-11423,
   		11491,-11587,11681,-11777,11827,-11903,11959,-12041,
   		12109,-12197,12263,-12343,12413,-12487,12541,-12611,
   		12671,-12757,12829,-12917,12979,-13043,13127,-13187,
   		13291,-13367,13451,-13523,13619,-13691,13751,-13829,
   		13901,-13967,14057,-14153,14249,-14341,14419,-14489,
   		14557,-14633,14717,-14767,14831,-14897,14983,-15083,
   		15149,-15233,15289,-15359,15427,-15497,15583,-15649,
   		15733,-15791,15881,-15937,16057,-16097,16189,-16267,
   		16363,-16447,16529,-16619,16691,-16763,16879,-16937,
   		17021,-17093,17183,-17257,17341,-17401,17477,-17551,
   		17623,-17713,17791,-17891,17957,-18041,18097,-18169,
   		18233,-18307,18379,-18451,18523,-18637,18731,-18803,
   		18919,-19031,19121,-19211,19273,-19381,19429,-19477
	} ;
#endif

int  	main			ARGS((int,char **));
int  	Usage			ARGS((void));
void  	comprexx		ARGS((char **));
void  	compdir			ARGS((char *));
void  	compress		ARGS((int,int));
/* CJH */
//void  	decompress		ARGS((int,int));
int 	is_compressed		ARGS((char *,int));
void  	read_error		ARGS((void));
void  	write_error		ARGS((void));
int 	abort_compress	ARGS((void));
void  	prratio			ARGS((FILE *,long,long));
int  	about			ARGS((void));

/*****************************************************************
 * TAG( main )
 *
 * Algorithm from "A Technique for High Performance Data Compression",
 * Terry A. Welch, IEEE Computer Vol 17, No 6 (June 1984), pp 8-19.
 *
 * Usage: compress [-dfvc] [-b bits] [file ...]
 * Inputs:
 *   -d:     If given, decompression is done instead.
 *
 *   -c:     Write output on stdout, don't remove original.
 *
 *   -b:     Parameter limits the max number of bits/code.
 *
 *   -f:     Forces output file to be generated, even if one already
 *           exists, and even if no space is saved by compressing.
 *           If -f is not used, the user will be prompted if stdin is
 *           a tty, otherwise, the output file will not be overwritten.
 *
 *   -v:     Write compression statistics
 *
 *   -r:     Recursive. If a filename is a directory, descend
 *           into it and compress everything in it.
 *
 * file ...:
 *           Files to be compressed.  If none specified, stdin is used.
 * Outputs:
 *   file.Z:     Compressed form of file with same mode, owner, and utimes
 *   or stdout   (if stdin used as input)
 *
 * Assumptions:
 *   When filenames are given, replaces with the compressed version
 *   (.Z suffix) only if the file decreases in size.
 *
 * Algorithm:
 *   Modified Lempel-Ziv method (LZW).  Basically finds common
 *   substrings and replaces them with a variable size code.  This is
 *   deterministic, and can be done on the fly.  Thus, the decompression
 *   procedure needs no input table, but tracks the way the table was built.
 */ 
/* CJH */
#ifdef DO_ARGV
int
main(argc, argv)
	REG1	int 	 argc;
	REG2	char	*argv[];
	{
    	REG3	char		**filelist;
		REG4	char		**fileptr;

    	if (fgnd_flag = (signal(SIGINT, SIG_IGN) != SIG_IGN))
			signal(SIGINT, (SIG_TYPE)abort_compress);

		signal(SIGTERM, (SIG_TYPE)abort_compress);
#ifndef DOS
		signal(SIGHUP, (SIG_TYPE)abort_compress);
#endif

#ifdef COMPATIBLE
    	nomagic = 1;	/* Original didn't have a magic number */
#endif

    	filelist = (char **)malloc(argc*sizeof(char *));
    	if (filelist == NULL)
		{
			fprintf(stderr, "Cannot allocate memory for file list.\n");
			return 1;
		}
    	fileptr = filelist;
    	*filelist = NULL;

    	if((progname = strrchr(argv[0], '/')) != 0)
			progname++;
		else
			progname = argv[0];

    	if (strcmp(progname, "uncompress") == 0
	    || strcmp(progname, "uncompress.real") == 0)
			do_decomp = 1;
		else
		if (strcmp(progname, "zcat") == 0)
			do_decomp = zcat_flg = 1;

    	/* Argument Processing
     	 * All flags are optional.
     	 * -V => print Version; debug verbose
     	 * -d => do_decomp
     	 * -v => unquiet
     	 * -f => force overwrite of output file
     	 * -n => no header: useful to uncompress old files
     	 * -b maxbits => maxbits.  If -b is specified, then maxbits MUST be given also.
     	 * -c => cat all output to stdout
     	 * -C => generate output compatible with compress 2.0.
     	 * -r => recursively compress directories
     	 * if a string is left, must be an input filename.
     	 */

    	for (argc--, argv++; argc > 0; argc--, argv++)
		{
			if (**argv == '-')
			{/* A flag argument */
		    	while (*++(*argv))
				{/* Process all flags in this arg */
					switch (**argv)
					{
			    	case 'V':
						about();
						return 0;
			    	case 's':
						silent = 1;
						quiet = 1;
						break;

			    	case 'v':
						silent = 0;
						quiet = 0;
						break;

			    	case 'd':
						do_decomp = 1;
						break;

			    	case 'f':
			    	case 'F':
						force = 1;
						break;

			    	case 'n':
						nomagic = 1;
						break;

			    	case 'C':
						block_mode = 0;
						break;

			    	case 'b':
						if (!ARGVAL())
						{
					    	fprintf(stderr, "Missing maxbits\n");
					    	Usage();
						return 1;
						}

						maxbits = atoi(*argv);
						goto nextarg;

		    		case 'c':
						zcat_flg = 1;
						break;

			    	case 'q':
						quiet = 1;
						break;
			    	case 'r':
			    	case 'R':
#ifdef	RECURSIVE
						recursive = 1;
#else
						fprintf(stderr, "%s -r not available (due to missing directory functions)\n", *argv);
#endif
						break;

			    	default:
						fprintf(stderr, "Unknown flag: '%c'; ", **argv);
						Usage();
						return 1;
					}
		    	}
			}
			else
			{
		    	*fileptr++ = *argv;	/* Build input file list */
		    	*fileptr = NULL;
			}

nextarg:	continue;
    	}

    	if (maxbits < INIT_BITS)	maxbits = INIT_BITS;
    	if (maxbits > BITS) 		maxbits = BITS;
    	
	if (*filelist != NULL)
		{
      		for (fileptr = filelist; *fileptr; fileptr++)
				comprexx(fileptr);
    	}
		else
		{/* Standard input */
			ifname = "";
			exit_code = 0;
			remove_ofname = 0;

			if (do_decomp == 0)
			{
				compress(0, 1);

				if (zcat_flg == 0 && !quiet)
				{
					fprintf(stderr, "Compression: ");
					prratio(stderr, bytes_in-bytes_out, bytes_in);
					fprintf(stderr, "\n");
				}

				if (bytes_out >= bytes_in && !(force))
					exit_code = 2;
			}
			//else
				//decompress(0, 1);
		}
		
		//int rsize = 0;
		//char input_buffer[64] = { 0 };

		//rsize = read(0, input_buffer, sizeof(input_buffer));
		//decompress(input_buffer, rsize);

		//return (exit_code== -1) ? 1:exit_code;
	}

int
Usage()
	{
		fprintf(stderr, "\
Usage: %s [-dfvcVr] [-b maxbits] [file ...]\n\
       -d   If given, decompression is done instead.\n\
       -c   Write output on stdout, don't remove original.\n\
       -b   Parameter limits the max number of bits/code.\n", progname);
		fprintf(stderr, "\
       -f   Forces output file to be generated, even if one already.\n\
            exists, and even if no space is saved by compressing.\n\
            If -f is not used, the user will be prompted if stdin is.\n\
            a tty, otherwise, the output file will not be overwritten.\n\
       -v   Write compression statistics.\n\
       -V   Output vesion and compile options.\n\
       -r   Recursive. If a filename is a directory, descend\n\
            into it and compress everything in it.\n");

    		return 1;
	}

void
comprexx(fileptr)
	char	**fileptr;
	{
		int		fdin;
		int		fdout;
		char	tempname[MAXPATHLEN];

		if (strlen(*fileptr) > sizeof(tempname) - 3) {
			fprintf(stderr, "Pathname too long: %s\n", *fileptr);
			exit_code = 1;
			return;
		}

		strcpy(tempname,*fileptr);
		errno = 0;

#ifdef	LSTAT
		if (lstat(tempname,&infstat) == -1)
#else
		if (stat(tempname,&infstat) == -1)
#endif
		{
		  	if (do_decomp)
			{
	    		switch (errno)
				{
		    	case ENOENT:	/* file doesn't exist */
	      			/*
	      			** if the given name doesn't end with .Z, try appending one
	      			** This is obviously the wrong thing to do if it's a 
	      			** directory, but it shouldn't do any harm.
	      			*/
		      		if (strcmp(tempname + strlen(tempname) - 2, ".Z") != 0)
					{
						strcat(tempname,".Z");
						errno = 0;
#ifdef	LSTAT
						if (lstat(tempname,&infstat) == -1)
#else
						if (stat(tempname,&infstat) == -1)
#endif
						{
						  	perror(tempname);
							exit_code = 1;
						  	return;
						}

						if ((infstat.st_mode & S_IFMT) != S_IFREG)
						{
							fprintf(stderr, "%s: Not a regular file.\n", tempname);
							exit_code = 1;
							return ;
						}
		      		}
		      		else
					{
						perror(tempname);
						exit_code = 1;
						return;
		      		}

		      		break;

	    		default:
		      		perror(tempname);
					exit_code = 1;
		      		return;
	    		}
	  		}
	  		else
			{
	      		perror(tempname);
				exit_code = 1;
	      		return;
	  		}
		}

		switch (infstat.st_mode & S_IFMT)
		{
		case S_IFDIR:	/* directory */
#ifdef	RECURSIVE
		  	if (recursive)
		    	compdir(tempname);
		  	else
#endif
			if (!quiet)
		    	fprintf(stderr,"%s is a directory -- ignored\n", tempname);
		  	break;

		case S_IFREG:	/* regular file */
		  	if (do_decomp != 0)
			{/* DECOMPRESSION */
		    	if (!zcat_flg)
				{
			      	if (strcmp(tempname + strlen(tempname) - 2, ".Z") != 0)
					{
						if (!quiet)
		  					fprintf(stderr,"%s - no .Z suffix\n",tempname);

						return;
	      			}
		    	}

				strcpy(ofname, tempname);

				/* Strip of .Z suffix */

				if (strcmp(tempname + strlen(tempname) - 2, ".Z") == 0)
			  		ofname[strlen(tempname) - 2] = '\0';
	   		}
	   		else
			{/* COMPRESSION */
		    	if (!zcat_flg)
				{
					if (strcmp(tempname + strlen(tempname) - 2, ".Z") == 0)
					{
		 	 			fprintf(stderr, "%s: already has .Z suffix -- no change\n", tempname);
			  			return;
					}

					if (infstat.st_nlink > 1 && (!force))
					{
			  			fprintf(stderr, "%s has %d other links: unchanged\n",
										tempname, infstat.st_nlink - 1);
						exit_code = 1;
			  			return;
					}
				}

				strcpy(ofname, tempname);
				strcat(ofname, ".Z");
    		}

	    	if ((fdin = open(ifname = tempname, O_RDONLY|O_BINARY)) == -1)
			{
		      	perror(tempname);
				exit_code = 1;
				return;
	    	}

    		if (zcat_flg == 0)
			{
				int				c;
				int				s;
				struct stat		statbuf;
				struct stat		statbuf2;

				if (stat(ofname, &statbuf) == 0)
				{
					if ((s = strlen(ofname)) > 8)
					{
						c = ofname[s-1];
						ofname[s-1] = '\0';

						statbuf2 = statbuf;

						if (!stat(ofname, &statbuf2) &&
							statbuf.st_mode  == statbuf2.st_mode &&
							statbuf.st_ino   == statbuf2.st_ino &&
							statbuf.st_dev   == statbuf2.st_dev &&
							statbuf.st_uid   == statbuf2.st_uid &&
							statbuf.st_gid   == statbuf2.st_gid &&
							statbuf.st_size  == statbuf2.st_size &&
							statbuf.st_atime == statbuf2.st_atime &&
							statbuf.st_mtime == statbuf2.st_mtime &&
							statbuf.st_ctime == statbuf2.st_ctime)
						{
							fprintf(stderr, "%s: filename too long to tack on .Z\n", tempname);
							exit_code = 1;
							return;
						}

						ofname[s-1] = (char)c;
					}

					if (!force)
					{
		    			inbuf[0] = 'n';

		    			fprintf(stderr, "%s already exists.\n", ofname);

		    			if (fgnd_flag && isatty(0))
						{
							fprintf(stderr, "Do you wish to overwrite %s (y or n)? ", ofname);
							fflush(stderr);
	
			    			if (read(0, inbuf, 1) > 0)
							{
								if (inbuf[0] != '\n')
								{
									do
									{
										if (read(0, inbuf+1, 1) <= 0)
										{
											perror("stdin");
											break;
										}
									}
									while (inbuf[1] != '\n');
								}
							}
							else
								perror("stdin");
		    			}

		    			if (inbuf[0] != 'y')
						{
							fprintf(stderr, "%s not overwritten\n", ofname);
							exit_code = 1;
							return;
		    			}
					}

					if (unlink(ofname))
					{
						fprintf(stderr, "Can't remove old output file\n");
						perror(ofname);
						exit_code = 1;
						return ;
					}
				}

		    	if ((fdout = open(ofname, O_WRONLY|O_CREAT|O_EXCL|O_BINARY,0600)) == -1)
				{
			      	perror(tempname);
					return;
		    	}

				if ((s = strlen(ofname)) > 8)
				{
					if (fstat(fdout, &statbuf))
					{
						fprintf(stderr, "Can't get status op output file\n");
						perror(ofname);
						exit_code = 1;
						return ;
					}

					c = ofname[s-1];
					ofname[s-1] = '\0';
					statbuf2 = statbuf;

					if (!stat(ofname, &statbuf2) &&
						statbuf.st_mode  == statbuf2.st_mode &&
						statbuf.st_ino   == statbuf2.st_ino &&
						statbuf.st_dev   == statbuf2.st_dev &&
						statbuf.st_uid   == statbuf2.st_uid &&
						statbuf.st_gid   == statbuf2.st_gid &&
						statbuf.st_size  == statbuf2.st_size &&
						statbuf.st_atime == statbuf2.st_atime &&
						statbuf.st_mtime == statbuf2.st_mtime &&
						statbuf.st_ctime == statbuf2.st_ctime)
					{
						fprintf(stderr, "%s: filename too long to tack on .Z\n", tempname);

						if (unlink(ofname))
						{
							fprintf(stderr, "can't remove bad output file\n");
							perror(ofname);
						}
						exit_code = 1;
						return;
					}

					ofname[s-1] = (char)c;
				}

				if(!quiet)
					fprintf(stderr, "%s: ", tempname);

				remove_ofname = 1;
    		}
			else
			{
				fdout = 1;
				ofname[0] = '\0';
				remove_ofname = 0;
			}

    		if (do_decomp == 0)
				compress(fdin, fdout);
    		else
				decompress(fdin, fdout);

			close(fdin);

			if (fdout != 1 && close(fdout))
				write_error();

			if ( (bytes_in == 0) && (force == 0 ) )
			{
				if (remove_ofname)
				{
					if(!quiet)
						fprintf(stderr, "No compression -- %s unchanged\n", ifname);
					if (unlink(ofname))	/* Remove input file */
					{
						fprintf(stderr, "\nunlink error (ignored) ");
	    				perror(ofname);
						exit_code = 1;
					}
		
					remove_ofname = 0;
					exit_code = 2;
				}
			}
			else
    		if (zcat_flg == 0)
			{
		    	struct utimbuf	timep;

		    	if (!do_decomp && bytes_out >= bytes_in && (!force))
				{/* No compression: remove file.Z */
					if(!quiet)
						fprintf(stderr, "No compression -- %s unchanged\n", ifname);

			    	if (unlink(ofname))
					{
						fprintf(stderr, "unlink error (ignored) ");
						perror(ofname);
					}

					remove_ofname = 0;
					exit_code = 2;
		    	}
				else
				{/* ***** Successful Compression ***** */
					if(!quiet)
					{
						fprintf(stderr, " -- replaced with %s",ofname);

						if (!do_decomp)
						{
							fprintf(stderr, " Compression: ");
							prratio(stderr, bytes_in-bytes_out, bytes_in);
						}

						fprintf(stderr, "\n");
					}

					timep.actime = infstat.st_atime;
					timep.modtime = infstat.st_mtime;

					if (utime(ofname, &timep))
					{
						fprintf(stderr, "\nutime error (ignored) ");
				    	perror(ofname);
						exit_code = 1;
					}

#ifndef	AMIGA
					if (chmod(ofname, infstat.st_mode & 07777))		/* Copy modes */
					{
						fprintf(stderr, "\nchmod error (ignored) ");
				    	perror(ofname);
						exit_code = 1;
					}
#ifndef	DOS
					if (chown(ofname, infstat.st_uid, infstat.st_gid))	/* Copy ownership */
					{
						fprintf(stderr, "\nchown error (ignored) ");
						perror(ofname);
						exit_code = 1;
					}
#endif
#endif
					remove_ofname = 0;

					if (unlink(ifname))	/* Remove input file */
					{
						fprintf(stderr, "\nunlink error (ignored) ");
	    				perror(ifname);
						exit_code = 1;
					}
    			}
    		}

			if (exit_code == -1)
				exit_code = 0;

	  		break;

		default:
	  		fprintf(stderr,"%s is not a directory or a regular file - ignored\n",
			  		tempname);
	  		break;
		}
	}
#endif // DO_ARGV

#ifdef	RECURSIVE
void
compdir(dir)
	REG3	char	*dir;
	{
#ifndef	DIRENT
		REG1 	struct direct	*dp;
#else
		REG1 	struct dirent	*dp;
#endif
		REG2	DIR				*dirp;
		char					 nbuf[MAXPATHLEN];
		char					*nptr = nbuf;

		dirp = opendir(dir);

		if (dirp == NULL)
		{
			printf("%s unreadable\n", dir);		/* not stderr! */
			return ;
		}
		/*
		** WARNING: the following algorithm will occasionally cause
		** compress to produce error warnings of the form "<filename>.Z
		** already has .Z suffix - ignored". This occurs when the
		** .Z output file is inserted into the directory below
		** readdir's current pointer.
		** These warnings are harmless but annoying. The alternative
		** to allowing this would be to store the entire directory
		** list in memory, then compress the entries in the stored
		** list. Given the depth-first recursive algorithm used here,
		** this could use up a tremendous amount of memory. I don't
		** think it's worth it. -- Dave Mack
		*/

		while (dp = readdir(dirp))
		{
			if (dp->d_ino == 0)
				continue;

			if (strcmp(dp->d_name,".") == 0 || strcmp(dp->d_name,"..") == 0)
				continue;

			if ((strlen(dir)+strlen(dp->d_name)+1) < (MAXPATHLEN - 1))
			{
			  	strcpy(nbuf,dir);
			  	strcat(nbuf,"/");
			  	strcat(nbuf,dp->d_name);
		  		comprexx(&nptr);
			}
			else
		  		fprintf(stderr,"Pathname too long: %s/%s\n", dir, dp->d_name);
  		}

		closedir(dirp);

		return;
	}
#endif
/*
 * compress fdin to fdout
 *
 * Algorithm:  use open addressing double hashing (no chaining) on the 
 * prefix code / next character combination.  We do a variant of Knuth's
 * algorithm D (vol. 3, sec. 6.4) along with G. Knott's relatively-prime
 * secondary probe.  Here, the modular division first probe is gives way
 * to a faster exclusive-or manipulation.  Also do block compression with
 * an adaptive reset, whereby the code table is cleared when the compression
 * ratio decreases, but after the table fills.  The variable-length output
 * codes are re-sized at this point, and a special CLEAR code is generated
 * for the decompressor.  Late addition:  construct the table according to
 * file size for noticeable speed improvement on small files.  Please direct
 * questions about this implementation to ames!jaw.
 */
void
compress(fdin, fdout)
	int		fdin;
	int		fdout;
	{
		REG2	long		hp;
		REG3	int			rpos;
#if REGISTERS >= 5
		REG5	long		fc;
#endif
		REG6	int			outbits;
		REG7    int			rlop;
		REG8	int			rsize;
		REG9	int			stcode;
		REG10	code_int	free_ent;
		REG11	int			boff;
		REG12	int			n_bits;
		REG13	int			ratio;
		REG14	long		checkpoint;
		REG15	code_int	extcode;
		union
		{
			long			code;
			struct
			{
				char_type		c;
				unsigned short	ent;
			} e;
		} fcode;

		ratio = 0;
		checkpoint = CHECK_GAP;
		extcode = MAXCODE(n_bits = INIT_BITS)+1;
		stcode = 1;
		free_ent = FIRST;

		memset(outbuf, 0, sizeof(outbuf));
		bytes_out = 0; bytes_in = 0;
		outbuf[0] = MAGIC_1;
		outbuf[1] = MAGIC_2;
		outbuf[2] = (char)(maxbits | block_mode);
		boff = outbits = (3<<3);
		fcode.code = 0;

		clear_htab();

		while ((rsize = read(fdin, inbuf, IBUFSIZ)) > 0)
		{
			if (bytes_in == 0)
			{
				fcode.e.ent = inbuf[0];
				rpos = 1;
			}
			else
				rpos = 0;

			rlop = 0;

			do
			{
				if (free_ent >= extcode && fcode.e.ent < FIRST)
				{
					if (n_bits < maxbits)
					{
						boff = outbits = (outbits-1)+((n_bits<<3)-
								  	((outbits-boff-1+(n_bits<<3))%(n_bits<<3)));
						if (++n_bits < maxbits)
							extcode = MAXCODE(n_bits)+1;
						else
							extcode = MAXCODE(n_bits);
					}
					else
					{
						extcode = MAXCODE(16)+OBUFSIZ;
						stcode = 0;
					}
				}

				if (!stcode && bytes_in >= checkpoint && fcode.e.ent < FIRST)
				{
					REG1 long int rat;

					checkpoint = bytes_in + CHECK_GAP;

					if (bytes_in > 0x007fffff)
					{							/* shift will overflow */
						rat = (bytes_out+(outbits>>3)) >> 8;

						if (rat == 0)				/* Don't divide by zero */
							rat = 0x7fffffff;
						else
							rat = bytes_in / rat;
					}
					else
						rat = (bytes_in << 8) / (bytes_out+(outbits>>3));	/* 8 fractional bits */
					if (rat >= ratio)
						ratio = (int)rat;
					else
					{
						ratio = 0;
						clear_htab();
						output(outbuf,outbits,CLEAR,n_bits);
						boff = outbits = (outbits-1)+((n_bits<<3)-
								  	((outbits-boff-1+(n_bits<<3))%(n_bits<<3)));
						extcode = MAXCODE(n_bits = INIT_BITS)+1;
						free_ent = FIRST;
						stcode = 1;
					}
				}

				if (outbits >= (OBUFSIZ<<3))
				{
					if (write(fdout, outbuf, OBUFSIZ) != OBUFSIZ)
						write_error();

					outbits -= (OBUFSIZ<<3);
					boff = -(((OBUFSIZ<<3)-boff)%(n_bits<<3));
					bytes_out += OBUFSIZ;

					memcpy(outbuf, outbuf+OBUFSIZ, (outbits>>3)+1);
					memset(outbuf+(outbits>>3)+1, '\0', OBUFSIZ);
				}

				{
					REG1	int		i;

					i = rsize-rlop;

					if ((code_int)i > extcode-free_ent)	i = (int)(extcode-free_ent);
					if (i > ((sizeof(outbuf) - 32)*8 - outbits)/n_bits)
						i = ((sizeof(outbuf) - 32)*8 - outbits)/n_bits;
					
					if (!stcode && (long)i > checkpoint-bytes_in)
						i = (int)(checkpoint-bytes_in);

					rlop += i;
					bytes_in += i;
				}

				goto next;
hfound:			fcode.e.ent = codetabof(hp);
next:  			if (rpos >= rlop)
	   				goto endlop;
next2: 			fcode.e.c = inbuf[rpos++];
#ifndef FAST
				{
					REG1 	code_int	i;
#if REGISTERS >= 5
					fc = fcode.code;
#else
#	define			fc fcode.code
#endif
					hp = (((long)(fcode.e.c)) << (BITS-8)) ^ (long)(fcode.e.ent);

					if ((i = htabof(hp)) == fc)
						goto hfound;

					if (i != -1)
					{
						REG4 long		disp;

						disp = (HSIZE - hp)-1;	/* secondary hash (after G. Knott) */

						do
						{
							if ((hp -= disp) < 0)	hp += HSIZE;

							if ((i = htabof(hp)) == fc)
								goto hfound;
						}
						while (i != -1);
					}
				}
#else
				{
					REG1 long	i;
					REG4 long	p;
#if REGISTERS >= 5
					fc = fcode.code;
#else
#	define			fc fcode.code
#endif
					hp = ((((long)(fcode.e.c)) << (HBITS-8)) ^ (long)(fcode.e.ent));

					if ((i = htabof(hp)) == fc)	goto hfound;
					if (i == -1)				goto out;

					p = primetab[fcode.e.c];
lookup:				hp = (hp+p)&HMASK;
					if ((i = htabof(hp)) == fc)	goto hfound;
					if (i == -1)				goto out;
					hp = (hp+p)&HMASK;
					if ((i = htabof(hp)) == fc)	goto hfound;
					if (i == -1)				goto out;
					hp = (hp+p)&HMASK;
					if ((i = htabof(hp)) == fc)	goto hfound;
					if (i == -1)				goto out;
					goto lookup;
				}
out:			;
#endif
				output(outbuf,outbits,fcode.e.ent,n_bits);

				{
#if REGISTERS < 5
#	undef	fc
					REG1 long	fc;
					fc = fcode.code;
#endif
					fcode.e.ent = fcode.e.c;


					if (stcode)
					{
						codetabof(hp) = (unsigned short)free_ent++;
						htabof(hp) = fc;
					}
				} 

				goto next;

endlop:			if (fcode.e.ent >= FIRST && rpos < rsize)
					goto next2;

				if (rpos > rlop)
				{
					bytes_in += rpos-rlop;
					rlop = rpos;
				}
			}
			while (rlop < rsize);
		}

		if (rsize < 0)
			read_error();

		if (bytes_in > 0)
			output(outbuf,outbits,fcode.e.ent,n_bits);

		if (write(fdout, outbuf, (outbits+7)>>3) != (outbits+7)>>3)
			write_error();

		bytes_out += (outbits+7)>>3;

		return;
	}

/*
 * Decompress stdin to stdout.  This routine adapts to the codes in the
 * file building the "string" table on-the-fly; requiring no table to
 * be stored in the compressed file.  The tables used herein are shared
 * with those of the compress() routine.  See the definitions above.
 */

/* CJH
void
decompress(fdin, fdout)
	int		fdin;
	int		fdout;
	{
*/

int is_compressed(char *inbuffer, int insize)
{
	    REG2 	char_type 		*stackp;
	    REG3	code_int		 code;
    	REG4	int				 finchar;
		REG5	code_int		 oldcode;
		REG6	code_int		 incode;
		REG7	int				 inbits;
		REG8	int				 posbits;
		REG9	int				 outpos;
		// CJH REG10	int				 insize;
		REG11	int				 bitmask;
		REG12	code_int		 free_ent;
		REG13	code_int		 maxcode;
		REG14	code_int		 maxmaxcode;
		REG15	int				 n_bits;
		REG16	int				 rsize;

		bytes_in = 0;
		bytes_out = 0;
		// CJH insize = 0;

		/* CJH
		while (insize < 3 && (rsize = read(fdin, inbuf+insize, IBUFSIZ)) > 0)
			insize += rsize;
		*/
		if (insize < sizeof(inbuf))
		{
			memcpy(inbuf, inbuffer, insize);
			rsize = insize;
		}
		else
		{
			memcpy(inbuf, inbuffer, sizeof(inbuf));
			rsize = insize = sizeof(inbuf);
		}

		if (insize < 3 || inbuf[0] != MAGIC_1 || inbuf[1] != MAGIC_2)
		{
			if (rsize < 0)
				read_error();

			if (insize > 0)
			{
				//fprintf(stderr, "%s: not in compressed format\n",
				//					(ifname[0] != '\0'? ifname : "stdin"));
				exit_code = 1;
			}

			return 0;
		}

		maxbits = inbuf[2] & BIT_MASK;
		block_mode = inbuf[2] & BLOCK_MODE;
		maxmaxcode = MAXCODE(maxbits);

		if (maxbits > BITS)
		{
			//fprintf(stderr,
			//		"%s: compressed with %d bits, can only handle %d bits\n",
			//		(*ifname != '\0' ? ifname : "stdin"), maxbits, BITS);
			exit_code = 4;
			return 0;
		}

		bytes_in = insize;
	    maxcode = MAXCODE(n_bits = INIT_BITS)-1;
		bitmask = (1<<n_bits)-1;
		oldcode = -1;
		finchar = 0;
		outpos = 0;
		posbits = 3<<3;

	    free_ent = ((block_mode) ? FIRST : 256);

		clear_tab_prefixof();	/* As above, initialize the first
								   256 entries in the table. */

	    for (code = 255 ; code >= 0 ; --code)
			tab_suffixof(code) = (char_type)code;

		do
		{
resetbuf:	;
			{
				REG1	 int	i;
				int				e;
				int				o;

				o = posbits >> 3;
				e = o <= insize ? insize - o : 0;

				for (i = 0 ; i < e ; ++i)
					inbuf[i] = inbuf[i+o];

				insize = e;
				posbits = 0;
			}

			if (insize < sizeof(inbuf)-IBUFSIZ)
			{
				rsize = 0;
				/*
				if ((rsize = read(fdin, inbuf+insize, IBUFSIZ)) < 0)
				{
					printf("Read error!!\n");
					read_error();
				}
				*/

				insize += rsize;
			}

			inbits = ((rsize > 0) ? (insize - insize%n_bits)<<3 : 
									(insize<<3)-(n_bits-1));

			while (inbits > posbits)
			{
				if (free_ent > maxcode)
				{
					posbits = ((posbits-1) + ((n_bits<<3) -
									 (posbits-1+(n_bits<<3))%(n_bits<<3)));

					++n_bits;
					if (n_bits == maxbits)
						maxcode = maxmaxcode;
					else
					    maxcode = MAXCODE(n_bits)-1;

					bitmask = (1<<n_bits)-1;
					goto resetbuf;
				}

				input(inbuf,posbits,code,n_bits,bitmask);

				if (oldcode == -1)
				{
					if (code >= 256) {
						//fprintf(stderr, "oldcode:-1 code:%i\n", (int)(code));
						//fprintf(stderr, "uncompress: corrupt input\n");
						//abort_compress();
						return 0;
					}
					outbuf[outpos++] = (char_type)(finchar = (int)(oldcode = code));
					continue;
				}

				if (code == CLEAR && block_mode)
				{
					clear_tab_prefixof();
	    			free_ent = FIRST - 1;
					posbits = ((posbits-1) + ((n_bits<<3) -
								(posbits-1+(n_bits<<3))%(n_bits<<3)));
				    maxcode = MAXCODE(n_bits = INIT_BITS)-1;
					bitmask = (1<<n_bits)-1;
					goto resetbuf;
				}

				incode = code;
			    stackp = de_stack;

				if (code >= free_ent)	/* Special case for KwKwK string.	*/
				{
					if (code > free_ent)
					{
						//REG1 char_type 		*p;

						posbits -= n_bits;
						//p = &inbuf[posbits>>3];

						//fprintf(stderr, "insize:%d posbits:%d inbuf:%02X %02X %02X %02X %02X (%d)\n", insize, posbits,
						//		p[-1],p[0],p[1],p[2],p[3], (posbits&07));
			    		//fprintf(stderr, "uncompress: corrupt input\n");
						//abort_compress();
						return 0;
					}

        	    	*--stackp = (char_type)finchar;
		    		code = oldcode;
				}

				while ((cmp_code_int)code >= (cmp_code_int)256)
				{ /* Generate output characters in reverse order */
			    	*--stackp = tab_suffixof(code);
			    	code = tab_prefixof(code);
				}

				*--stackp =	(char_type)(finchar = tab_suffixof(code));

			/* And put them out in forward order */

				{
					REG1 int	i;

					if (outpos+(i = (de_stack-stackp)) >= OBUFSIZ)
					{
						do
						{
							if (i > OBUFSIZ-outpos) i = OBUFSIZ-outpos;

							if (i > 0)
							{
								memcpy(outbuf+outpos, stackp, i);
								outpos += i;
							}

							if (outpos >= OBUFSIZ)
							{
								/*
								if (write(fdout, outbuf, outpos) != outpos)
									write_error();
								*/

								outpos = 0;
							}
							stackp+= i;
						}
						while ((i = (de_stack-stackp)) > 0);
					}
					else
					{
						memcpy(outbuf+outpos, stackp, i);
						outpos += i;
					}
				}

				if ((code = free_ent) < maxmaxcode) /* Generate the new entry. */
				{
			    	tab_prefixof(code) = (unsigned short)oldcode;
			    	tab_suffixof(code) = (char_type)finchar;
	    			free_ent = code+1;
				} 

				oldcode = incode;	/* Remember previous code.	*/
			}

			bytes_in += rsize;
	    }
		while (rsize > 0);

		/*
		if (outpos > 0 && write(fdout, outbuf, outpos) != outpos)
			write_error();
		*/

		return 1;
	}

void
read_error()
	{
		fprintf(stderr, "\nread error on");
	    perror((ifname[0] != '\0') ? ifname : "stdin");
		abort_compress();
	}

void
write_error()
	{
		fprintf(stderr, "\nwrite error on");
	    perror((ofname[0] != '\0') ? ofname : "stdout");
		abort_compress();
	}

int
abort_compress()
	{
		if (remove_ofname)
	    	unlink(ofname);

		return 1;
	}

void
prratio(stream, num, den)
	FILE		*stream;
	long int	 num;
	long int	 den;
	{
		REG1 int q;			/* Doesn't need to be long */

		if (den > 0)
		{
			if (num > 214748L) 
				q = (int)(num/(den/10000L));	/* 2147483647/10000 */
			else
				q = (int)(10000L*num/den);		/* Long calculations, though */
		}
		else
			q = 10000;

		if (q < 0)
		{
			putc('-', stream);
			q = -q;
		}

		fprintf(stream, "%d.%02d%%", q / 100, q % 100);
	}

int
about()
	{
		/* CJH */
		//fprintf(stderr, "Compress version: %s, compiled: %s\n", version_id, COMPILE_DATE);
		fprintf(stderr, "Compile options:\n        ");
#if BYTEORDER == 4321 && NOALLIGN == 1
		fprintf(stderr, "USE_BYTEORDER, ");
#endif
#ifdef FAST
		fprintf(stderr, "FAST, ");
#endif
#ifdef vax
		fprintf(stderr, "vax, ");
#endif
#ifdef DIRENT
		fprintf(stderr,"DIRENT, ");
#endif
#ifdef SYSDIR
		fprintf(stderr,"SYSDIR, ");
#endif
#ifdef NO_UCHAR
		fprintf(stderr, "NO_UCHAR, ");
#endif
#ifdef SIGNED_COMPARE_SLOW
		fprintf(stderr, "SIGNED_COMPARE_SLOW, ");
#endif
#ifdef MAXSEG_64K
		fprintf(stderr, "MAXSEG_64K, ");
#endif
#ifdef DOS
		fprintf(stderr, "DOS, ");
#endif
#ifdef DEBUG
		fprintf(stderr, "DEBUG, ");
#endif
#ifdef LSTAT
		fprintf(stderr, "LSTAT, ");
#endif
		fprintf(stderr, "\n        REGISTERS=%d IBUFSIZ=%d, OBUFSIZ=%d, BITS=%d\n", 
			REGISTERS, IBUFSIZ, OBUFSIZ, BITS);

		fprintf(stderr, "\n\
Author version 4.2 (Speed improvement & source cleanup):\n\
     Peter Jannesen  (peter@ncs.nl)\n\
\n\
Author version 4.1 (Added recursive directory compress):\n\
     Dave Mack  (csu@alembic.acs.com)\n\
\n\
Authors version 4.0 (World release in 1985):\n\
     Spencer W. Thomas, Jim McKie, Steve Davies,\n\
     Ken Turkowski, James A. Woods, Joe Orost\n");

		return 0;
	}
