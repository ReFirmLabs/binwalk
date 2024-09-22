use crate::signatures;
use crate::structures::pchrom::parse_pchrom_header;

pub const DESCRIPTION: &str = "Intel serial flash for PCH ROM";

pub fn pch_rom_magic() -> Vec<Vec<u8>> {
    return vec![b"\x5a\xa5\xf0\x0f".to_vec()];
}

pub fn pch_rom_parser(file_data: &Vec<u8>, offset: usize) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {

    const MAGIC_OFFSET: usize = 16;

    let mut result = signatures::common::SignatureResult {
                                            size: 0,
                                            offset: 0,
                                            description: DESCRIPTION.to_string(),
                                            ..Default::default()
    };

    // Sanity check the offset where the magic bytes were found
    if offset >= MAGIC_OFFSET {
        // Set the reported starting offset of this signature
        result.offset = offset - MAGIC_OFFSET;

        if let Ok(pchrom_header) = parse_pchrom_header(&file_data[result.offset..]) {
            result.size = pchrom_header.header_size + pchrom_header.data_size;
            return Ok(result);
        }
    }
    
    return Err(signatures::common::SignatureError);
}
