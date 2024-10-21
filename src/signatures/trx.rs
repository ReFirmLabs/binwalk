use crate::extractors::trx::extract_trx_partitions;
use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_HIGH};
use crate::structures::trx::parse_trx_header;

/// Human readable description
pub const DESCRIPTION: &str = "TRX firmware image";

/// TRX magic bytes
pub fn trx_magic() -> Vec<Vec<u8>> {
    vec![b"HDR0".to_vec()]
}

/// Validates a TRX signature
pub fn trx_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Success return value
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_HIGH,
        ..Default::default()
    };

    // Do a dry run to validate the TRX data
    let dry_run = extract_trx_partitions(file_data, offset, None);

    if dry_run.success {
        if let Some(trx_total_size) = dry_run.size {
            // Dry run successful, parse the TRX header and return a useful description
            if let Ok(trx_header) = parse_trx_header(&file_data[offset..]) {
                result.size = trx_total_size;
                result.description = format!("{}, version {}, partition count: {}, header size: {} bytes, total size: {} bytes", result.description,
                                                                                                                                 trx_header.version,
                                                                                                                                 trx_header.partitions.len(),
                                                                                                                                 trx_header.header_size,
                                                                                                                                 result.size);
                return Ok(result);
            }
        }
    }

    Err(SignatureError)
}
