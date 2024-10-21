use crate::structures::common::{self, StructureError};

/// Stores info about a YAFFS object
#[derive(Debug, Default, Clone)]
pub struct YAFFSObject {
    // All that is needed for now is the object type; this may be updated in the future as necessary
    pub obj_type: usize,
}

/// Partially parse a YAFFS object header
pub fn parse_yaffs_obj_header(
    header_data: &[u8],
    endianness: &str,
) -> Result<YAFFSObject, StructureError> {
    // The name checksum field is unused and should be 0xFFFF
    const UNUSED: usize = 0xFFFF;

    // First part of an object header
    let yaffs_object_structure = vec![
        ("type", "u32"),
        ("parent_id", "u32"),
        ("name_checksum", "u16"),
    ];

    // Allowed object types
    let allowed_types: Vec<usize> = vec![0, 1, 2, 3, 4, 5];

    // Parse the object header
    if let Ok(obj_header) = common::parse(header_data, &yaffs_object_structure, endianness) {
        // Validate that the header looks sane
        if allowed_types.contains(&obj_header["type"])
            && (obj_header["parent_id"] > 0)
            && (obj_header["name_checksum"] == UNUSED)
        {
            return Ok(YAFFSObject {
                obj_type: obj_header["type"],
            });
        }
    }

    Err(StructureError)
}

/// Stores info about a YAFFS file header
#[derive(Debug, Default, Clone)]
pub struct YAFFSFileHeader {
    // Only this field is needed, for now. Struct may be updated in the future if necessary.
    pub file_size: usize,
}

/// Partially parse a YAFFS file header
pub fn parse_yaffs_file_header(
    header_data: &[u8],
    endianness: &str,
) -> Result<YAFFSFileHeader, StructureError> {
    // Second part of an object header (after the name field)
    let yaffs_file_info = vec![
        ("mode", "u32"),
        ("uid", "u32"),
        ("gid", "u32"),
        ("atime", "u32"),
        ("mtime", "u32"),
        ("ctime", "u32"),
        ("file_size", "u32"),
    ];

    if let Ok(file_info) = common::parse(header_data, &yaffs_file_info, endianness) {
        return Ok(YAFFSFileHeader {
            file_size: file_info["file_size"],
        });
    }

    Err(StructureError)
}
