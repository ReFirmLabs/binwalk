use crate::signatures;
use crate::structures::qnx::parse_ifs_header;

pub const IFS_DESCRIPTION: &str = "QNX IFS image";

pub fn qnx_ifs_magic() -> Vec<Vec<u8>> {
    /*
     * Assumes little endian.
     * Includes the magic bytes (u32) and version number (u16), which must be 1.
     */
    return vec![b"\xEB\x7E\xFF\x00\x01\x00".to_vec()];
}

pub fn qnx_ifs_parser(
    file_data: &Vec<u8>,
    offset: usize,
) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {
    let mut result = signatures::common::SignatureResult {
        size: 0,
        offset: offset,
        description: IFS_DESCRIPTION.to_string(),
        ..Default::default()
    };

    let available_data: usize = file_data.len() - offset;

    if let Ok(ifs_header) = parse_ifs_header(&file_data[offset..]) {
        // Set the total size of this signature
        result.size = ifs_header.total_size;

        // Sanity check that the total size doesn't exceed the available data size
        if result.size <= available_data {
            result.description =
                format!("{}, total size: {} bytes", result.description, result.size);
            return Ok(result);
        }
    }

    return Err(signatures::common::SignatureError);
}
