use crate::common;
use crate::signatures::common::{
    SignatureError, SignatureResult, CONFIDENCE_HIGH, CONFIDENCE_MEDIUM,
};
use crate::structures::cramfs::parse_cramfs_header;

/// Human readable description
pub const DESCRIPTION: &str = "CramFS filesystem";

/// This is technically the CramFS "signature", not the magic bytes, but it's endian-agnostic
pub fn cramfs_magic() -> Vec<Vec<u8>> {
    vec![b"Compressed ROMFS".to_vec()]
}

/// Parse and validate the CramFS header
pub fn cramfs_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Some constant relative offsets
    const SIGNATURE_OFFSET: usize = 16;
    const CRC_START_OFFSET: usize = 32;
    const CRC_END_OFFSET: usize = 36;

    let mut result = SignatureResult {
        offset: offset - SIGNATURE_OFFSET,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_HIGH,
        ..Default::default()
    };

    if let Some(cramfs_header_data) = file_data.get(result.offset..) {
        // Parse the CramFS header; also validates that the reported size is greater than the header size
        if let Ok(cramfs_header) = parse_cramfs_header(cramfs_header_data) {
            // Update the reported size
            result.size = cramfs_header.size;

            if let Some(cramfs_image_data) =
                file_data.get(result.offset..result.offset + result.size)
            {
                /*
                 * Create a copy of the cramfs image; we have to NULL out the checksum field to calculate the CRC.
                 * This typically shouldn't be too bad on performance, CramFS images are usually relatively small.
                 */
                let mut cramfs_image: Vec<u8> = cramfs_image_data.to_vec();

                // Null out the checksum field
                for crc_byte in cramfs_image
                    .iter_mut()
                    .take(CRC_END_OFFSET)
                    .skip(CRC_START_OFFSET)
                {
                    *crc_byte = 0;
                }

                // For displaying an error message in the description
                let mut error_message: &str = "";

                // On CRC error, lower confidence and report the checksum error
                // (have seen partially corrupted images that still extract Ok)
                if common::crc32(&cramfs_image) != cramfs_header.checksum {
                    error_message = " (checksum error)";
                    result.confidence = CONFIDENCE_MEDIUM;
                }

                result.description = format!(
                    "{}, {} endian, {} files, total size: {} bytes{}",
                    result.description,
                    cramfs_header.endianness,
                    cramfs_header.file_count,
                    cramfs_header.size,
                    error_message
                );
                return Ok(result);
            }
        }
    }

    Err(SignatureError)
}
