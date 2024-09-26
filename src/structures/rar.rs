use crate::structures;
use std::collections::HashMap;

#[derive(Debug, Default, Clone)]
pub struct RarArchiveHeader {
    pub version: usize,
}

pub fn parse_rar_archive_header(
    rar_data: &[u8],
) -> Result<RarArchiveHeader, structures::common::StructureError> {
    let archive_header_structure =
        vec![("magic_p1", "u32"), ("magic_p2", "u16"), ("version", "u8")];

    // Version field of 0 indicates RARv4; version field of 1 indicates RARv5
    let version_map: HashMap<usize, usize> = HashMap::from([(0, 4), (1, 5)]);

    // Parse the header
    if let Ok(archive_header) = structures::common::parse(rar_data, &archive_header_structure, "little") {

        // Make sure the version number is one of the known versions
        if version_map.contains_key(&archive_header["version"]) {
            return Ok(RarArchiveHeader {
                version: version_map[&archive_header["version"]],
            });
        }
    }

    return Err(structures::common::StructureError);
}
