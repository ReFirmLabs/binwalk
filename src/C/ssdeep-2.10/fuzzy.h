/*
 * Copyright (C) ManTech International Corporation 2010
 * Copyright (C) Kyrus 2012
 * Copyright (C) 2013 Helmut Grohne <helmut@subdivi.de>
 *
 * $Id: fuzzy.h 180 2013-06-10 23:24:26Z jessekornblum $
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 *
 * Earlier versions of this code can be found at:
 *     http://ssdeep.sf.net/
 */

/// \mainpage
/// This is the documentation for the fuzzy hashing API from ssdeep.
///
/// There is a complete function reference in fuzzy.h.
///
/// The most recent version of this documentation can be found
/// at http://ssdeep.sourceforge.net/.
///
/// \copydoc fuzzy.h
///
/// \version 3.0
///
/// \author Jesse Kornblum, research@jessekornblum.com
/// \author Helmut Grohne, helmut@subdivi.de

/// \file fuzzy.h
/// \brief
/// These functions allow a programmer to compute the fuzzy hashes
/// (also called the context-triggered piecewise hashes) of
/// \link fuzzy_hash_buf() a buffer
/// of text @endlink,
/// \link fuzzy_hash_filename() the contents of a file on the disk @endlink,
/// and
/// @link fuzzy_hash_file() the contents of
/// an open file handle @endlink .
/// There is also a function to
/// @link fuzzy_compare() compute the
/// similarity between any two fuzzy signatures @endlink.


#include <stdint.h>
#include <stdio.h>

#ifdef __cplusplus
extern "C" {
#endif

#ifndef FUZZY_H
#define FUZZY_H

/**
 * @brief fuzzy_digest flag indicating to eliminate sequences of more than
 *        three identical characters
 */
#define FUZZY_FLAG_ELIMSEQ 0x1u
/**
 * @brief fuzzy_digest flag indicating not to truncate the second part to
 *        SPAMSUM_LENGTH/2 characters.
 */
#define FUZZY_FLAG_NOTRUNC 0x2u

struct fuzzy_state;

/**
 * @brief Construct a fuzzy_state object and return it.
 *
 * To use it call fuzzy_update and fuzzy_digest on it. It must be disposed
 * with fuzzy_free.
 * @return the constructed fuzzy_state or NULL on failure
 */
extern /*@only@*/ /*@null@*/ struct fuzzy_state *fuzzy_new(void);

/**
 * @brief Feed the data contained in the given buffer to the state.
 *
 * When an error occurs, the state is undefined. In that case it must not be
 * passed to any function besides fuzzy_free.
 * @param buffer The data to be hashes
 * @param buffer_size The length of the given buffer
 * @return zero on success, non-zero on error
 */
extern int fuzzy_update(struct fuzzy_state *state, 
			const unsigned char *buffer,
			size_t buffer_size);

/**
 * @brief Obtain the fuzzy hash from the state.
 *
 * This operation does not change the state at all. It reports the hash for the
 * concatenation of the data previously fed using fuzzy_update. 
 * @param result Where the fuzzy hash is stored. This variable
 * must be allocated to hold at least FUZZY_MAX_RESULT bytes.
 * @param flags is a bitwise or of FUZZY_FLAG_* macros. The absence of flags is
 * represented by a zero.
 * @return zero on success, non-zero on error
 */
extern int fuzzy_digest(const struct fuzzy_state *state,
			/*@out@*/ char *result, 
			unsigned int flags);
  
/**
 * @brief Dispose a fuzzy state.
 */
extern void fuzzy_free(/*@only@*/ struct fuzzy_state *state);
  
/**
 * @brief Compute the fuzzy hash of a buffer
 *
 * The computes the fuzzy hash of the first buf_len bytes of the buffer.
 * It is the caller's responsibility to append the filename,
 * if any, to result after computation. 
 * @param buf The data to be fuzzy hashed
 * @param buf_len The length of the data being hashed
 * @param result Where the fuzzy hash of buf is stored. This variable
 * must be allocated to hold at least FUZZY_MAX_RESULT bytes.
 * @return Returns zero on success, non-zero on error.
 */
extern int fuzzy_hash_buf(const unsigned char *buf, 
			  uint32_t buf_len,
			  /*@out@*/ char *result);

/**
 * @brief Compute the fuzzy hash of a file using an open handle
 *
 * Computes the fuzzy hash of the contents of the open file, starting
 * at the beginning of the file. When finished, the file pointer is
 * returned to its original position. If an error occurs, the file 
 * pointer's value is undefined.
 * It is the callers's responsibility to append the filename
 * to the result after computation.
 * @param handle Open handle to the file to be hashed
 * @param result Where the fuzzy hash of the file is stored. This 
 * variable must be allocated to hold at least FUZZY_MAX_RESULT bytes.
 * @return Returns zero on success, non-zero on error
 */
extern int fuzzy_hash_file(FILE *handle, /*@out@*/ char *result);

/**
 * @brief Compute the fuzzy hash of a stream using an open handle
 *
 * Computes the fuzzy hash of the contents of the open stream, starting at the
 * current file position until reaching EOF. Unlike fuzzy_hash_file the stream
 * is never seeked. If an error occurs, the result as well as the file position
 * are undefined.
 * It is the callers's responsibility to append the filename
 * to the result after computation.
 * @param handle Open handle to the stream to be hashed
 * @param result Where the fuzzy hash of the file is stored. This 
 * variable must be allocated to hold at least FUZZY_MAX_RESULT bytes.
 * @return Returns zero on success, non-zero on error
 */
extern int fuzzy_hash_stream(FILE *handle, /*@out@*/ char *result);

/**
 * @brief Compute the fuzzy hash of a file
 *
 * Opens, reads, and hashes the contents of the file 'filename' 
 * The result must be allocated to hold FUZZY_MAX_RESULT characters. 
 * It is the caller's responsibility to append the filename
 * to the result after computation. 
 * @param filename The file to be hashed
 * @param result Where the fuzzy hash of the file is stored. This 
 * variable must be allocated to hold at least FUZZY_MAX_RESULT bytes.
 * @return Returns zero on success, non-zero on error. 
 */
extern int fuzzy_hash_filename(const char *filename, /*@out@*/ char * result);

/// Computes the match score between two fuzzy hash signatures.
/// @return Returns a value from zero to 100 indicating the
/// match score of the 
/// two signatures. A match score of zero indicates the sigantures
/// did not match. When an error occurs, such as if one of the
/// inputs is NULL, returns -1.
extern int fuzzy_compare(const char *sig1, const char *sig2);

/** Length of an individual fuzzy hash signature component. */
#define SPAMSUM_LENGTH 64

/** The longest possible length for a fuzzy hash signature
 * (without the filename) */
#define FUZZY_MAX_RESULT (2 * SPAMSUM_LENGTH + 20)

#ifdef __cplusplus
} 
#endif

#endif
