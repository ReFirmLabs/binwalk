use crate::signatures;
use crate::structures::cab::parse_cab_header;

pub const DESCRIPTION: &str = "Microsoft Cabinet archive";

pub fn cab_magic() -> Vec<Vec<u8>> {
    // Includes the magic bytes and the following reserved1 header entry, which must be 0
    return vec![b"MSCF\x00\x00\x00\x00".to_vec()];
}

pub fn cab_parser(file_data: &Vec<u8>, offset: usize) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {

    if let Ok(cab_header) = parse_cab_header(&file_data[offset..]) {
        return Ok(signatures::common::SignatureResult {
                                            description: format!("{}, file count: {}, folder count: {}, header size: {}, total size: {} bytes", DESCRIPTION,
                                                                                                                                                cab_header.file_count,
                                                                                                                                                cab_header.folder_count,
                                                                                                                                                cab_header.header_size,
                                                                                                                                                cab_header.total_size),
                                            offset: offset,
                                            size: cab_header.total_size,
                                            confidence: signatures::common::CONFIDENCE_MEDIUM,
                                            ..Default::default()
        });
    }

    return Err(signatures::common::SignatureError);
}
