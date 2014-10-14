#include <stdio.h>
#include <string.h>
#include "tinfl.c"

// Checks to see if the first block of data in in_buf is valid zlib compressed data.
// Returns 1 if valid, 0 if invalid.
int is_valid_zlib_data(char *in_buf, size_t in_buf_size);

#define BLOCK_SIZE (32*1024)
char *inflate_block(char *buf, size_t buf_size)
{
	size_t out_size = BLOCK_SIZE;
	return (char *) tinfl_decompress_mem_to_heap((const void *) buf, buf_size, (size_t *) &out_size, 0);
}

/* CJH */

int is_deflated_callback(const void *pBuf, int len, void *pUser)
{
	int *decomp_size = pUser;

	*decomp_size += len;

	if(len > 0)
	{
		return 1;
	}

        return 0;
}

/*
 * Tries to determine if a given buffer contains valid deflated data.
 *
 * @buf                  - The buffer of data to check for deflated data.
 * @buf_size             - The size of @buf.
 * @includes_zlib_header - Set to 1 if the buffer should start with a valid zlib header.
 * 
 * Returns the size of the inflated data if @buf inflated to a value larger than 32KB, 
 * or if it contained a valid zlib header/footer; else, returns 0.
 *
 * Thus, it is recommended to provide more than 32KB of data in @buf for the most accurate results.
 */
int is_deflated(char *buf, size_t buf_size, int includes_zlib_header)
{
  int flags = TINFL_FLAG_HAS_MORE_INPUT;
  int retval = 0, decomp_size = 0;

  if(includes_zlib_header)
  {
    flags |= TINFL_FLAG_PARSE_ZLIB_HEADER | TINFL_FLAG_COMPUTE_ADLER32;
  }

  retval = tinfl_decompress_mem_to_callback(buf, &buf_size, is_deflated_callback, (void *) &decomp_size, flags);

  if(retval == 1 || decomp_size > BLOCK_SIZE)
  {
    return decomp_size;
  }

  return 0;
}

int inflate_raw_file_callback(const void *pBuf, int len, void *pUser)
{
	if(fwrite(pBuf, 1, len, (FILE *) pUser) == len)
	{
		return 1;
	}
	
	return 0;
}

/* Inflates a file containing raw deflated data.
 *
 * @in_file  - Input file containing raw deflated data.
 * @out_file - Output file where inflated data will be saved.
 *
 * Returns void.
 */
void inflate_raw_file(char *in_file, char *out_file)
{
	char *compressed_data = NULL;
	size_t in_size = 0, nbytes = 0;
	FILE *fp_in = NULL, *fp_out = NULL;

	fp_in = fopen(in_file, "rb");
	if(fp_in)
	{
		fp_out = fopen(out_file, "wb");
		if(fp_out)
		{
	
			fseek(fp_in, 0L, SEEK_END);
			in_size = ftell(fp_in);
			fseek(fp_in, 0L, SEEK_SET);

			compressed_data = malloc(in_size);
			if(compressed_data)
			{
				memset(compressed_data, 0, in_size);

				nbytes = fread(compressed_data, 1, in_size, fp_in);
				if(nbytes > 0)
				{
					tinfl_decompress_mem_to_callback(compressed_data, &nbytes, inflate_raw_file_callback, (void *) fp_out, 0);
				}
				
				free(compressed_data);
			}
		}
	}

	if(fp_in) fclose(fp_in);
	if(fp_out) fclose(fp_out);

	return;
}

#ifdef MAIN
int main(int argc, char *argv[])
{
	if(argc != 3)
	{
		fprintf(stderr, "Usage: %s <input file> <output file>\n", argv[0]);
		return EXIT_FAILURE;
	}

	inflate_raw_file(argv[1], argv[2]);
	
	return EXIT_SUCCESS;
}
#endif
