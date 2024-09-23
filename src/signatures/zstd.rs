use crate::signatures;
use crate::structures::zstd::{parse_block_header, parse_zstd_header};

pub const DESCRIPTION: &str = "ZSTD compressed data";

pub fn zstd_magic() -> Vec<Vec<u8>> {
    return vec![b"\x28\xb5\x2f\xfd".to_vec()];
}

pub fn zstd_parser(
    file_data: &Vec<u8>,
    offset: usize,
) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {
    const EOF_CHECKSUM_SIZE: usize = 4;

    // More or less arbitrarily chosen
    const MIN_BLOCK_COUNT: usize = 2;

    let mut result = signatures::common::SignatureResult {
        offset: offset,
        description: DESCRIPTION.to_string(),
        confidence: signatures::common::CONFIDENCE_HIGH,
        ..Default::default()
    };

    // Parse the ZSTD header
    if let Ok(zstd_header) = parse_zstd_header(&file_data[offset..]) {
        /*
         * The first block header starts immediately after the ZSTD header, BUT there may be optional header fields present.
         * Must parse the frame header descriptor bit fields to determine total size of the header.
         */
        let mut next_block_header_start = offset + zstd_header.fixed_header_size;

        // If single segment flag is not set, then window descriptor byte is present in the header
        if zstd_header.single_segment_flag == false {
            next_block_header_start += 1;
        }

        // If the dictionary ID flag is non-zero, its value represents the size of the dictionary ID field; else, this field does not exist
        if zstd_header.dictionary_id_flag == 1 {
            next_block_header_start += 1;
        } else if zstd_header.dictionary_id_flag == 2 {
            next_block_header_start += 2;
        } else if zstd_header.dictionary_id_flag == 3 {
            next_block_header_start += 4;
        }

        /*
         * If the frame content flag is 0 and the single segment flag is set, then the frame content header field is 1 byte in length;
         * else, the frame content flag indicates the size of the grame content header field.
         */
        if zstd_header.frame_content_flag == 0 && zstd_header.single_segment_flag == true {
            next_block_header_start += 1;
        } else if zstd_header.frame_content_flag == 1 {
            next_block_header_start += 2;
        } else if zstd_header.frame_content_flag == 2 {
            next_block_header_start += 4;
        } else if zstd_header.frame_content_flag == 3 {
            next_block_header_start += 8;
        }

        // Keep a count of how many blocks we've processed
        let mut block_count: usize = 0;

        // We now know where the first block header starts, loop through all the blocks to determine where the ZSTD data ends
        while file_data.len() > next_block_header_start {
            // Parse the block header
            match parse_block_header(&file_data[next_block_header_start..]) {
                Err(_) => {
                    break;
                }

                Ok(block_header) => {
                    // Block header looks valid, increment block counter
                    block_count += 1;

                    // The next block header should start at the end of this block; note that the reported block size does not include the size of the block header
                    next_block_header_start += block_header.header_size + block_header.block_size;

                    // Was this the last block?
                    if block_header.last_block == true {
                        // Update the total size, which is the difference between the end of the last block and the start of the ZSTD header
                        result.size = next_block_header_start - offset;

                        // If a checksum is included at the end of the block stream, add the checksum size to the total size
                        if zstd_header.content_checksum_present {
                            result.size += EOF_CHECKSUM_SIZE;
                        }

                        // Make sure we've processed more than one block; if so, return Ok, else break and return Err below
                        if block_count >= MIN_BLOCK_COUNT {
                            result.description = format!(
                                "{}, total size: {} bytes",
                                result.description, result.size
                            );
                            return Ok(result);
                        } else {
                            break;
                        }
                    }
                }
            }
        }
    }

    return Err(signatures::common::SignatureError);
}
