use crate::structures::common::{self, StructureError};

/// Struct to store parsed jzlzma (mark_rootfs_lzma wrapper) header data
#[derive(Debug, Default, Clone)]
pub struct JzlzmaHeader {
    pub payload_size: usize,
    pub dictionary_size: usize,
    pub decompressed_size: usize,
}

/// Magic bytes for the mark_rootfs_lzma wrapper: 0x27051956 (LE)
pub const JZ_MAGIC: u32 = 0x27051956;

/// Sane maximum for dictionary size (256 MiB)
const MAX_DICT_SIZE: usize = 0x10000000;

/// Sane maximum for uncompressed size (256 MiB)
const MAX_UNCOMP_SIZE: usize = 0x10000000;

/// Parse a jzlzma mark_rootfs_lzma wrapper header
///
/// Layout (all little-endian):
///   [0..4)   payload_size  — size of data after this wrapper header
///   [4..8)   magic         — 0x27051956
///   [8..12)  dictionary_size
///   [12..16) uncompressed_size
///   [16..)   jzlzma bit-stream
pub fn parse_jzlzma_header(data: &[u8]) -> Result<JzlzmaHeader, StructureError> {
    let structure = vec![
        ("payload_size", "u32"),
        ("magic", "u32"),
        ("dictionary_size", "u32"),
        ("uncompressed_size", "u32"),
    ];

    if let Ok(header) = common::parse(data, &structure, "little") {
        if header["magic"] == JZ_MAGIC as usize {
            if header["dictionary_size"] > 0 && header["dictionary_size"] < MAX_DICT_SIZE {
                if header["uncompressed_size"] > 0
                    && header["uncompressed_size"] < MAX_UNCOMP_SIZE
                {
                    return Ok(JzlzmaHeader {
                        payload_size: header["payload_size"],
                        dictionary_size: header["dictionary_size"],
                        decompressed_size: header["uncompressed_size"],
                    });
                }
            }
        }
    }

    Err(StructureError)
}
