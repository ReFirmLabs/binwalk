use crate::signatures::common::{CONFIDENCE_HIGH, SignatureError, SignatureResult};
use crate::structures::matter_ota::parse_matter_ota_header;

/// Human readable description
pub const DESCRIPTION: &str = "Matter OTA firmware";

/// Matter OTA firmware images always start with these bytes
pub fn matter_ota_magic() -> Vec<Vec<u8>> {
    vec![b"\x1e\xf1\xee\x1b".to_vec()]
}

/// Validates the Matter OTA header
pub fn matter_ota_parser(
    file_data: &[u8],
    offset: usize,
) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        ..Default::default()
    };

    if let Ok(ota_header) = parse_matter_ota_header(&file_data[offset..]) {
        result.confidence = CONFIDENCE_HIGH;
        result.size = ota_header.header_size;
        result.description = format!(
            "{}, total size: {} bytes, tlv header size: {} bytes, vendor id: 0x{:x}, product id: 0x{:x}, version: {}, payload size: {} bytes, digest type: {}, payload digest: {}",
            result.description,
            ota_header.total_size,
            ota_header.header_size,
            ota_header.vendor_id,
            ota_header.product_id,
            ota_header.version,
            ota_header.payload_size,
            ota_header.image_digest_type,
            ota_header.image_digest,
        );

        return Ok(result);
    }
    Err(SignatureError)
}
