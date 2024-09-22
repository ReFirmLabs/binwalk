use crate::signatures;
use crate::structures::dtb::parse_dtb_header;

pub const DESCRIPTION: &str = "Device tree blob (DTB)";

pub fn dtb_magic() -> Vec<Vec<u8>> {
    return vec![b"\xD0\x0D\xFE\xED".to_vec()];
}

pub fn dtb_parser(file_data: &Vec<u8>, offset: usize) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {

    let mut result = signatures::common::SignatureResult {
                                            offset: offset,
                                            description: DESCRIPTION.to_string(),
                                            confidence: signatures::common::CONFIDENCE_MEDIUM,
                                            ..Default::default()
    };

    // Parse the DTB header
    if let Ok(dtb_header) = parse_dtb_header(&file_data[offset..]) {

        // Calculate the offsets of where the dt_struct and dt_strings end
        let dt_struct_end: usize = offset + dtb_header.struct_offset + dtb_header.struct_size;
        let dt_strings_end: usize = offset + dtb_header.strings_offset + dtb_header.strings_size;

        // Sanity check the dt_struct and dt_strings offsets
        if file_data.len() >= dt_struct_end && file_data.len() >= dt_strings_end {

            result.size = dtb_header.total_size;
            result.description = format!("{}, version: {}, CPU ID: {}, total size: {} bytes", result.description,
                                                                                              dtb_header.version,
                                                                                              dtb_header.cpu_id,
                                                                                              result.size);
            return Ok(result);
        }
    }

    return Err(signatures::common::SignatureError);
}
