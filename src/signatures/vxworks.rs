use crate::common::get_cstring;
use crate::extractors::vxworks::extract_symbol_table;
use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_HIGH, CONFIDENCE_LOW};

/// Human readable descriptions
pub const SYMTAB_DESCRIPTION: &str = "VxWorks symbol table";
pub const WIND_KERNEL_DESCRIPTION: &str = "VxWorks WIND kernel version";

/// WIND kernel version magic
pub fn wind_kernel_magic() -> Vec<Vec<u8>> {
    // Magic version string for WIND kernels
    vec![b"WIND version ".to_vec()]
}

/// VxWorks symbol table magic bytes
pub fn symbol_table_magic() -> Vec<Vec<u8>> {
    // These magic bytes match the type and group fields in the VxWorks symbol table, for both big and little endian targets
    vec![
        b"\x00\x00\x05\x00\x00\x00\x00\x00".to_vec(),
        b"\x00\x00\x07\x00\x00\x00\x00\x00".to_vec(),
        b"\x00\x00\x09\x00\x00\x00\x00\x00".to_vec(),
        b"\x00\x05\x00\x00\x00\x00\x00\x00".to_vec(),
        b"\x00\x07\x00\x00\x00\x00\x00\x00".to_vec(),
        b"\x00\x09\x00\x00\x00\x00\x00\x00".to_vec(),
    ]
}

/// Validates WIND kernel version signatures
pub fn wind_kernel_parser(
    file_data: &[u8],
    offset: usize,
) -> Result<SignatureResult, SignatureError> {
    // Length of the magic signatures bytes
    const MAGIC_SIZE: usize = 13;

    let mut result = SignatureResult {
        offset,
        description: WIND_KERNEL_DESCRIPTION.to_string(),
        confidence: CONFIDENCE_LOW,
        ..Default::default()
    };

    // Want the string that proceeds the magic bytes
    let version_offset: usize = offset + MAGIC_SIZE;

    if let Some(version_bytes) = file_data.get(version_offset..) {
        // The wind kernel magic bytes should be followed by a string containing the wind kernel version
        let version_string = get_cstring(version_bytes);

        // Make sure we got a string
        if !version_string.is_empty() {
            result.size = MAGIC_SIZE + version_string.len();
            result.description = format!("{} {}", result.description, version_string);
            return Ok(result);
        }
    }

    Err(SignatureError)
}

/// Validates VxWorks symbol table signatures
pub fn symbol_table_parser(
    file_data: &[u8],
    offset: usize,
) -> Result<SignatureResult, SignatureError> {
    // The magic bytes start at this offset from the beginning of the symbol table
    const MAGIC_OFFSET: usize = 8;

    let mut result = SignatureResult {
        description: SYMTAB_DESCRIPTION.to_string(),
        confidence: CONFIDENCE_HIGH,
        ..Default::default()
    };

    // The magic bytes are not at the beginning of the VxWorks symbol table; sanity check the specified offset
    if offset >= MAGIC_OFFSET {
        // Actual start of the symbol table
        let symtab_start: usize = offset - MAGIC_OFFSET;

        // Do a dry-run extraction of the symbol table
        let dry_run = extract_symbol_table(file_data, symtab_start, None);

        // If dry run was a success, this is very likely a valid symbol table
        if dry_run.success {
            // Get the size of the symbol table from the dry-run
            if let Some(symtab_size) = dry_run.size {
                result.size = symtab_size;
                result.offset = symtab_start;
                result.description =
                    format!("{}, total size: {} bytes", result.description, result.size);

                return Ok(result);
            }
        }
    }

    Err(SignatureError)
}
