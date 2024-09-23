use crate::signatures;

pub const DESCRIPTION: &str = "CFE bootloader";

pub fn cfe_magic() -> Vec<Vec<u8>> {
    return vec![b"CFE1CFE1".to_vec()];
}

pub fn cfe_parser(
    _file_data: &Vec<u8>,
    offset: usize,
) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {
    const CFE_MAGIC_OFFSET: usize = 28;

    let mut result = signatures::common::SignatureResult {
        description: DESCRIPTION.to_string(),
        confidence: signatures::common::CONFIDENCE_LOW,
        ..Default::default()
    };

    // CFE signature starts 28 bytes from the beginning of the bootloader
    if offset >= CFE_MAGIC_OFFSET {
        // Adjust the reported starting offset accordingly
        result.offset = offset - CFE_MAGIC_OFFSET;

        // If this signature occurs at the very beginning of a file, our confidence is a bit higher...
        if result.offset == 0 {
            result.confidence = signatures::common::CONFIDENCE_MEDIUM;
        }

        return Ok(result);
    }

    return Err(signatures::common::SignatureError);
}
