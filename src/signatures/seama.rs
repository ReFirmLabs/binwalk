use crate::signatures;
use crate::structures::seama::parse_seama_header;

pub const DESCRIPTION: &str = "SEAMA firmware header";

pub fn seama_magic() -> Vec<Vec<u8>> {
    return vec![
        b"\x5E\xA3\xA4\x17\x00\x00".to_vec(),
        b"\x17\xA4\xA3\x5E\x00\x00".to_vec(),
    ];
}

pub fn seama_parser(file_data: &Vec<u8>, offset: usize) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {

    let mut result = signatures::common::SignatureResult {
                                            offset: offset,
                                            description: DESCRIPTION.to_string(),
                                            confidence: signatures::common::CONFIDENCE_LOW,
                                            ..Default::default()
    };

    if let Ok(seama_header) = parse_seama_header(&file_data[offset..]) {
        let total_size: usize = seama_header.header_size + seama_header.data_size;

        if file_data.len() >= (offset + total_size) {
            result.size = seama_header.header_size;
            result.description = format!("{}, header size: {} bytes, data size: {} bytes", result.description,
                                                                                           seama_header.header_size,
                                                                                           seama_header.data_size);
            return Ok(result);
        }
    }

    return Err(signatures::common::SignatureError);
}
