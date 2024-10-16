use crate::structures::common::{self, StructureError};

/// Struct to store some useful LUKS info
#[derive(Debug, Default, Clone)]
pub struct LUKSHeader {
    pub version: usize,
    pub hashfn: String,
}

/// Partially parses an ELF header
pub fn parse_luks_header(luks_data: &[u8]) -> Result<LUKSHeader, StructureError> {

    const HASHFN_START: usize = 72;
    const HASHFN_END: usize = 104;

    let luks_base_structure = vec![
        ("magic_1", "u32"),
        ("magic_2", "u16"),
        ("version", "u16"),
    ];

    let mut luks_hdr_info = LUKSHeader {
        ..Default::default()
    };

    if let Ok(luks_base) = common::parse(&luks_data, &luks_base_structure, "big") {
        if luks_base["version"] == 1 || luks_base["version"] == 2 {
            luks_hdr_info.version = luks_base["version"];
            if let Ok(hashfn) = String::from_utf8(luks_data[HASHFN_START..HASHFN_END].to_vec()) {
                luks_hdr_info.hashfn = hashfn;
                return Ok(luks_hdr_info);
            }
        }
    }

    return Err(StructureError);
}
