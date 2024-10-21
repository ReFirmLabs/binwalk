use crate::common::get_cstring;
use crate::structures::common::{self, StructureError};

/// Struct to store some useful LUKS info
#[derive(Debug, Default, Clone)]
pub struct LUKSHeader {
    pub version: usize,
    pub header_size: usize,
    pub hashfn: String,
    pub cipher_mode: String,
    pub cipher_algorithm: String,
}

/// Partially parses a LUKS header
pub fn parse_luks_header(luks_data: &[u8]) -> Result<LUKSHeader, StructureError> {
    // Start and end offsets of the cipher algorithm string
    const CIPHER_ALGO_START: usize = 8;
    const CIPHER_ALGO_END: usize = 40;

    // Start and end offsets of the cipher mode string
    const CIPHER_MODE_START: usize = 40;
    const CIPHER_MODE_END: usize = 72;

    // Start and end offsets of the hash function string
    const HASHFN_START: usize = 72;
    const HASHFN_END: usize = 104;

    // Minimum LUKS2 header size (assuming no JSON data)
    const LUKS2_MIN_HEADER_SIZE: usize = 4032;

    // https://en.wikipedia.org/wiki/Linux_Unified_Key_Setup
    // https://vhs.codeberg.page/post/external-backup-drive-encryption/assets/luks2_doc_wip.pdf
    let luks_base_structure = vec![
        ("magic_1", "u32"),
        ("magic_2", "u16"),
        ("version", "u16"),
        ("header_size", "u64"), // Only available in LUKS2
    ];

    let mut luks_hdr_info = LUKSHeader {
        ..Default::default()
    };

    if let Ok(luks_base) = common::parse(luks_data, &luks_base_structure, "big") {
        luks_hdr_info.version = luks_base["version"];

        // Both v1 and v2 include the hash function string at the same offset
        if let Some(hashfn_bytes) = luks_data.get(HASHFN_START..HASHFN_END) {
            luks_hdr_info.hashfn = get_cstring(hashfn_bytes);

            // Make sure there was actually a string at the expected hash function offset
            if !luks_hdr_info.hashfn.is_empty() {
                // Need to process v1 and v2 headers differently
                if luks_hdr_info.version == 1 {
                    // Get the cipher algorithm string
                    if let Some(cipher_algo_bytes) =
                        luks_data.get(CIPHER_ALGO_START..CIPHER_ALGO_END)
                    {
                        luks_hdr_info.cipher_algorithm = get_cstring(cipher_algo_bytes);

                        // Get the cipher mode string
                        if let Some(cipher_mode_bytes) =
                            luks_data.get(CIPHER_MODE_START..CIPHER_MODE_END)
                        {
                            luks_hdr_info.cipher_mode = get_cstring(cipher_mode_bytes);

                            // Make sure there were valid strings specified for both cipher algo and cipher mode
                            if !luks_hdr_info.cipher_mode.is_empty()
                                && !luks_hdr_info.cipher_algorithm.is_empty()
                            {
                                return Ok(luks_hdr_info);
                            }
                        }
                    }
                } else if luks_hdr_info.version == 2 {
                    // v2 doesn't have the same string entries, but does include a header size
                    luks_hdr_info.header_size = luks_base["header_size"];

                    // Sanity check the header size
                    if luks_hdr_info.header_size > LUKS2_MIN_HEADER_SIZE
                        && luks_hdr_info.header_size < luks_data.len()
                    {
                        return Ok(luks_hdr_info);
                    }
                }
            }
        }
    }

    Err(StructureError)
}
