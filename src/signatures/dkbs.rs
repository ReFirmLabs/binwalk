use crate::signatures::common::{
    SignatureError, SignatureResult, CONFIDENCE_HIGH, CONFIDENCE_MEDIUM,
};
use crate::structures::dkbs::parse_dkbs_header;

/// Human readable description
pub const DESCRIPTION: &str = "DKBS firmware header";

/// DKBS firmware magic
pub fn dkbs_magic() -> Vec<Vec<u8>> {
    vec![b"_dkbs_".to_vec()]
}

/// Validates the DKBS header
pub fn dkbs_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    const MAGIC_OFFSET: usize = 7;

    // Successful return value
    let mut result = SignatureResult {
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    // Sanity check the magic bytes offset
    if offset >= MAGIC_OFFSET {
        // Magic bytes occur 7 bytes into the actual firmware header
        result.offset = offset - MAGIC_OFFSET;

        // Parse the firmware header
        if let Ok(dkbs_header) = parse_dkbs_header(&file_data[result.offset..]) {
            // Calculate the total bytes available after the firmware header
            let available_data: usize = file_data.len() - result.offset;

            // Sanity check on the total reported DKBS firmware size
            if available_data >= (dkbs_header.header_size + dkbs_header.data_size) {
                // If this header starts at the beginning of the file, confidence is high
                if result.offset == 0 {
                    result.confidence = CONFIDENCE_HIGH;
                }

                // Report header size and description
                result.size = dkbs_header.header_size;
                result.description = format!(
                    "{}, board ID: {}, firmware version: {}, boot device: {}, endianness: {}, header size: {} bytes, data size: {}",
                    result.description, dkbs_header.board_id, dkbs_header.version, dkbs_header.boot_device, dkbs_header.endianness, dkbs_header.header_size, dkbs_header.data_size
                );

                // Return OK
                return Ok(result);
            }
        }
    }

    Err(SignatureError)
}
