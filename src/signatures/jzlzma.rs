use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_HIGH};
use crate::structures::jzlzma::parse_jzlzma_header;

/// Human readable description
pub const DESCRIPTION: &str = "jzlzma compressed data (Ingenic LZ77 variant), kernel or rootfs";

/// Magic bytes for jzlzma: 0x27051956 in little-endian
pub fn jzlzma_magic() -> Vec<Vec<u8>> {
    vec![b"\x56\x19\x05\x27".to_vec()]
}

/// Validate jzlzma signatures
pub fn jzlzma_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_HIGH,
        ..Default::default()
    };

    // The mark_rootfs_lzma wrapper has magic at bytes 4-7, so look back 4 bytes
    let header_offset = if offset >= 4 { offset - 4 } else { offset };

    if let Ok(jzlzma_header) = parse_jzlzma_header(&file_data[header_offset..]) {
        result.size = jzlzma_header.payload_size + 12; // 16-byte wrapper, but offset is at magic (byte 4)
        result.description = format!(
            "{}, payload size: {} bytes, dictionary size: {} bytes, uncompressed size: {} bytes",
            result.description,
            jzlzma_header.payload_size,
            jzlzma_header.dictionary_size,
            jzlzma_header.decompressed_size,
        );
        return Ok(result);
    }

    Err(SignatureError)
}
