use crate::common::is_offset_safe;
use crate::signatures;
use crate::structures::lzop::{
    parse_lzop_block_header, parse_lzop_eof_marker, parse_lzop_file_header,
};

pub const DESCRIPTION: &str = "LZO compressed data";

pub fn lzop_magic() -> Vec<Vec<u8>> {
    return vec![b"\x89LZO\x00\x0D\x0A\x1A\x0A".to_vec()];
}

pub fn lzop_parser(
    file_data: &Vec<u8>,
    offset: usize,
) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {
    let mut result = signatures::common::SignatureResult {
        size: 0,
        offset: offset,
        description: DESCRIPTION.to_string(),
        confidence: signatures::common::CONFIDENCE_HIGH,
        ..Default::default()
    };

    let available_data: usize = file_data.len() - offset;

    // Parse the LZOP file header
    if let Ok(lzop_header) = parse_lzop_file_header(&file_data[offset..]) {
        // Sanity check the reported header size
        if lzop_header.header_size < available_data {
            // Get the size of the compressed LZO data
            if let Ok(data_size) = get_lzo_data_size(
                &file_data[lzop_header.header_size..],
                lzop_header.block_checksum_present,
            ) {
                // Update the total size to include the LZO data
                result.size = lzop_header.header_size + data_size;
                result.description =
                    format!("{}, total size: {} bytes", result.description, result.size);
                return Ok(result);
            }
        }
    }

    return Err(signatures::common::SignatureError);
}

// Parse the LZO blocks to determine the size of the compressed data, including the terminating EOF marker
fn get_lzo_data_size(
    lzo_data: &[u8],
    compressed_checksum_present: bool,
) -> Result<usize, signatures::common::SignatureError> {
    const MIN_BLOCK_COUNT: usize = 2;

    let available_data = lzo_data.len();
    let mut last_offset = None;
    let mut data_size: usize = 0;
    let mut block_count: usize = 0;

    // Loop until we run out of data or an invalid block header is encountered
    while is_offset_safe(available_data, data_size, last_offset) {
        match parse_lzop_block_header(&lzo_data[data_size..], compressed_checksum_present) {
            Err(_) => {
                break;
            }

            Ok(block_header) => {
                block_count += 1;
                last_offset = Some(data_size);
                data_size += block_header.header_size
                    + block_header.compressed_size
                    + block_header.checksum_size;
            }
        }
    }

    // As a sanity check, make sure we processed some number of data blocks
    if block_count >= MIN_BLOCK_COUNT {
        // Process the EOF marker that should come at the end of the data blocks
        if let Some(eof_marker_data) = lzo_data.get(data_size..) {
            if let Ok(eof_marker_size) = parse_lzop_eof_marker(eof_marker_data) {
                data_size += eof_marker_size;
                return Ok(data_size);
            }
        }
    }

    return Err(signatures::common::SignatureError);
}
