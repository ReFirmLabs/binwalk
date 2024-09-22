use crate::signatures;
use crate::extractors::androidsparse::extract_android_sparse;
use crate::structures::androidsparse::parse_android_sparse_header;

pub const DESCRIPTION: &str = "Android sparse image";

pub fn android_sparse_magic() -> Vec<Vec<u8>> {
    return vec![b"\x3A\xFF\x26\xED".to_vec()];
}

pub fn android_sparse_parser(file_data: &Vec<u8>, offset: usize) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {

    let mut result = signatures::common::SignatureResult {
                                            size: 0,
                                            offset: offset,
                                            description: DESCRIPTION.to_string(),
                                            confidence: signatures::common::CONFIDENCE_HIGH,
                                            ..Default::default()
    };

    let dry_run = extract_android_sparse(file_data, offset, None);

    if dry_run.success == true {
        if let Some(total_size) = dry_run.size {
            if let Ok(header) = parse_android_sparse_header(&file_data[offset..]) {
                result.description = format!("{}, version {}.{}, header size: {}, block size: {}, chunk count: {}, total size: {} bytes", result.description,
                                                                                                                                          header.major_version,
                                                                                                                                          header.minor_version,
                                                                                                                                          header.header_size,
                                                                                                                                          header.block_size,
                                                                                                                                          header.chunk_count,
                                                                                                                                          total_size);
                result.size = total_size;
                return Ok(result);
            }
        }
    }

    return Err(signatures::common::SignatureError);
}
