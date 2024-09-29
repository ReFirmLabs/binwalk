use crate::extractors::trx::extract_trx_partitions;
use crate::signatures;
use crate::structures::trx::parse_trx_header;

pub const DESCRIPTION: &str = "TRX firmware image";

pub fn trx_magic() -> Vec<Vec<u8>> {
    return vec![b"HDR0".to_vec()];
}

pub fn trx_parser(
    file_data: &Vec<u8>,
    offset: usize,
) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {
    let mut result = signatures::common::SignatureResult {
        offset: offset,
        description: DESCRIPTION.to_string(),
        confidence: signatures::common::CONFIDENCE_HIGH,
        ..Default::default()
    };

    let dry_run = extract_trx_partitions(file_data, offset, None);

    if dry_run.success == true {
        if let Some(trx_total_size) = dry_run.size {
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

    return Err(signatures::common::SignatureError);
}
