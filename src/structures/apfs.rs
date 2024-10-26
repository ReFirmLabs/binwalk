use crate::structures::common::{self, StructureError};

/// Offset of the APFS magic bytes from the start of the APFS image
pub const MAGIC_OFFSET: usize = 0x20;

/// Struct to store APFS header info
#[derive(Debug, Default, Clone)]
pub struct APFSHeader {
    pub block_size: usize,
    pub block_count: usize,
}

/// Parses an APFS header
pub fn parse_apfs_header(apfs_data: &[u8]) -> Result<APFSHeader, StructureError> {
    // Partial APFS header, just to figure out the size of the image.
    // https://developer.apple.com/support/downloads/Apple-File-System-Reference.pdf
    let apfs_structure = vec![
        ("magic", "u32"),
        ("block_size", "u32"),
        ("block_count", "u64"),
    ];

    let apfs_struct_start = MAGIC_OFFSET;
    let apfs_struct_end = apfs_struct_start + common::size(&apfs_structure);

    // Parse the header
    if let Some(apfs_structure_data) = apfs_data.get(apfs_struct_start..apfs_struct_end) {
        if let Ok(apfs_header) = common::parse(apfs_structure_data, &apfs_structure, "little") {
            // Simple sanity check on the reported block data
            if apfs_header["block_size"] != 0 && apfs_header["block_count"] != 0 {
                return Ok(APFSHeader {
                    block_size: apfs_header["block_size"],
                    block_count: apfs_header["block_count"],
                });
            }
        }
    }

    Err(StructureError)
}
