use crate::extractors::androidsparse::extract_android_sparse;
use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_HIGH};
use crate::structures::androidsparse::parse_android_sparse_header;

/// Human readable description
pub const DESCRIPTION: &str = "Android sparse image";

/// Magic bytes for Android Sparse files
pub fn android_sparse_magic() -> Vec<Vec<u8>> {
    vec![b"\x3A\xFF\x26\xED".to_vec()]
}

/// Parses Android Sparse files
pub fn android_sparse_parser(
    file_data: &[u8],
    offset: usize,
) -> Result<SignatureResult, SignatureError> {
    // Default result, returned on success
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_HIGH,
        ..Default::default()
    };

    // Do a dry-run extraction
    let dry_run = extract_android_sparse(file_data, offset, None);

    if dry_run.success {
        if let Some(total_size) = dry_run.size {
            // Dry-run went OK, parse the header to get some useful info to report
            if let Ok(header) = parse_android_sparse_header(&file_data[offset..]) {
                // Update reported size and description
                result.size = total_size;
                result.description = format!("{}, version {}.{}, header size: {}, block size: {}, chunk count: {}, total size: {} bytes", result.description,
                                                                                                                                          header.major_version,
                                                                                                                                          header.minor_version,
                                                                                                                                          header.header_size,
                                                                                                                                          header.block_size,
                                                                                                                                          header.chunk_count,
                                                                                                                                          total_size);
                return Ok(result);
            }
        }
    }

    Err(SignatureError)
}
