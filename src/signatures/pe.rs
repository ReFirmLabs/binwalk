use crate::signatures;
use crate::structures::pe::parse_pe_header;

pub const DESCRIPTION: &str = "Windows PE binary";

pub fn pe_magic() -> Vec<Vec<u8>> {
    /*
     * This matches the first 16 bytes of a DOS header, from e_magic through e_ss.
     * Note that these values may differ in some special cases, but these are common ones.
     */
    return vec![
        b"\x4d\x5a\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00".to_vec(),
        b"\x4d\x5a\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00".to_vec(),
    ];
}

pub fn pe_parser(file_data: &Vec<u8>, offset: usize) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {

    let mut result = signatures::common::SignatureResult {
                                            size: 0,
                                            offset: offset,
                                            description: DESCRIPTION.to_string(),
                                            confidence: signatures::common::CONFIDENCE_MEDIUM,
                                            ..Default::default()
    };

    if let Ok(pe_header) = parse_pe_header(&file_data[offset..]) {
        result.description = format!("{}, machine type: {}", result.description, pe_header.machine);
        return Ok(result);
    }

    return Err(signatures::common::SignatureError);
}
