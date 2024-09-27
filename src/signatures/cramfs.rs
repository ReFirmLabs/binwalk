use crate::common;
use crate::signatures;
use crate::structures::cramfs::parse_cramfs_header;

pub const DESCRIPTION: &str = "CramFS filesystem";

pub fn cramfs_magic() -> Vec<Vec<u8>> {
    return vec![b"Compressed ROMFS".to_vec()];
}

pub fn cramfs_parser(
    file_data: &Vec<u8>,
    offset: usize,
) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {
    const SIGNATURE_OFFSET: usize = 16;
    const CRC_START_OFFSET: usize = 32;
    const CRC_END_OFFSET: usize = 36;

    let mut result = signatures::common::SignatureResult {
        offset: offset - SIGNATURE_OFFSET,
        description: DESCRIPTION.to_string(),
        confidence: signatures::common::CONFIDENCE_HIGH,
        ..Default::default()
    };

    if let Some(cramfs_header_data) = file_data.get(result.offset..) {
        // Parse the CramFS header
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
                for i in CRC_START_OFFSET..CRC_END_OFFSET {
                    cramfs_image[i] = 0;
                }

                // For displaying an error message in the description
                let mut error_message: &str = "";

                // On CRC error, lower confidence and report the checksum error
                if common::crc32(&cramfs_image) != cramfs_header.checksum {
                    error_message = " (checksum error)";
                    result.confidence = signatures::common::CONFIDENCE_MEDIUM;
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

    return Err(signatures::common::SignatureError);
}
