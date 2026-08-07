use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_MEDIUM};
use crate::structures::lz4l::{find_lz4l_compressed_length, parse_lz4l_header};

/// Human readable description
pub const DESCRIPTION: &str =
    "LZ4L compressed data (UNISOC NV-storage wrapper around a raw LZ4 block)";

/// Magic bytes for LZ4L: ASCII "LZ4L"
pub fn lz4l_magic() -> Vec<Vec<u8>> {
    vec![b"LZ4L".to_vec()]
}

/// Validate an LZ4L signature
///
/// Parses the 8-byte header, then finds the true compressed length by
/// searching for it (see `find_lz4l_compressed_length` for why -- the
/// format doesn't store it and the decompressor requires an exact bound).
/// `result.size` is the real, exact size of this structure, not an
/// estimate, so the scanner's own "does this fit in the file" bounds
/// check behaves correctly and downstream scanning resumes at the right
/// offset.
pub fn lz4l_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    const HEADER_SIZE: usize = 8;

    let mut result = SignatureResult {
        offset,
        confidence: CONFIDENCE_MEDIUM,
        description: DESCRIPTION.to_string(),
        ..Default::default()
    };

    let header = match parse_lz4l_header(&file_data[offset..]) {
        Ok(header) => header,
        Err(_) => return Err(SignatureError),
    };

    let compressed_data = match file_data.get(offset + HEADER_SIZE..) {
        Some(data) => data,
        None => return Err(SignatureError),
    };

    match find_lz4l_compressed_length(compressed_data, header.uncompressed_size) {
        Some(compressed_len) => {
            result.size = HEADER_SIZE + compressed_len;
            result.description = format!(
                "{}, uncompressed size: {} bytes",
                result.description, header.uncompressed_size,
            );
            Ok(result)
        }
        None => Err(SignatureError),
    }
}
