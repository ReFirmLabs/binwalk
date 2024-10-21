use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_LOW};

/// Human readable description
pub const EXCEPTION_HANDLER_DESCRIPTION: &str = "eCos kernel exception handler";

/// Big and little endian magic byte signatures for eCos kernel exception handlers (MIPS only)
pub fn exception_handler_magic() -> Vec<Vec<u8>> {
    /*
     * eCos kernel exception handlers
     *
     * mfc0    $k0, Cause       # Cause of last exception
     * nop                      # Some versions of eCos omit the nop
     * andi    $k0, 0x7F
     * li      $k1, 0xXXXXXXXX
     * add     $k1, $k0
     * lw      $k1, 0($k1)
     * jr      $k1
     * nop
     */
    vec![
        b"\x00\x68\x1A\x40\x00\x00\x00\x00\x7F\x00\x5A\x33".to_vec(),
        b"\x00\x68\x1A\x40\x7F\x00\x5A\x33".to_vec(),
        b"\x40\x1A\x68\x00\x00\x00\x00\x00\x33\x5A\x00\x7F".to_vec(),
        b"\x40\x1A\x68\x00\x33\x5A\x00\x7F".to_vec(),
    ]
}

/// Parses the eCos exception handler signature
pub fn exception_handler_parser(
    file_data: &[u8],
    offset: usize,
) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let mut result = SignatureResult {
        offset,
        description: EXCEPTION_HANDLER_DESCRIPTION.to_string(),
        confidence: CONFIDENCE_LOW,
        ..Default::default()
    };

    let mut endianness: &str = "big";

    // Detect endianess
    if file_data[offset] == 0 {
        endianness = "little";
    }

    result.description = format!("{}, MIPS {} endian", result.description, endianness);
    Ok(result)
}
