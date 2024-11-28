use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_HIGH};
use crate::signatures::openssl::openssl_crypt_parser;
use crate::structures::dlink_tlv::parse_dlink_tlv_header;

/// Human readable description
pub const DESCRIPTION: &str = "D-Link TLV firmware";

/// TLV firmware images always start with these bytes
pub fn dlink_tlv_magic() -> Vec<Vec<u8>> {
    vec![b"\x64\x80\x19\x40".to_vec()]
}

/// Validates the TLV header
pub fn dlink_tlv_parser(
    file_data: &[u8],
    offset: usize,
) -> Result<SignatureResult, SignatureError> {
    // Checksum calculation includes the 8-byte header that preceeds the actual payload data
    const CHECKSUM_OFFSET: usize = 8;

    // Successful return value
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_HIGH,
        ..Default::default()
    };

    // Parse the header
    if let Ok(tlv_header) = parse_dlink_tlv_header(&file_data[offset..]) {
        // Calculate the start and end offsets for the payload data over which the checksum is calculated
        let data_start = offset + tlv_header.header_size - CHECKSUM_OFFSET;
        let data_end = data_start + tlv_header.data_size + CHECKSUM_OFFSET;

        // Get the payload data and calculate the MD5 hash
        if let Some(payload_data) = file_data.get(data_start..data_end) {
            let payload_md5 = format!("{:x}", md5::compute(payload_data));

            // If the MD5 checksum exists, make sure it matches
            if tlv_header.data_checksum.is_empty() || payload_md5 == tlv_header.data_checksum {
                result.size = tlv_header.header_size + tlv_header.data_size;
                result.description = format!(
                    "{}, model name: {}, board ID: {}, header size: {} bytes, data size: {} bytes",
                    result.description,
                    tlv_header.model_name,
                    tlv_header.board_id,
                    tlv_header.header_size,
                    tlv_header.data_size,
                );

                // Check if the firmware data is OpenSSL encrypted
                if let Some(crypt_data) = file_data.get(offset + tlv_header.header_size..) {
                    if let Ok(openssl_signature) = openssl_crypt_parser(crypt_data, 0) {
                        result.description =
                            format!("{}, {}", result.description, openssl_signature.description);
                    }
                }

                return Ok(result);
            }
        }
    }

    Err(SignatureError)
}
