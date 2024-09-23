use crate::structures;

#[derive(Debug, Default, Clone)]
pub struct YAFFSObject {
    // All that is needed for now is the object type; this may be updated in the future as necessary
    pub obj_type: usize,
}

pub fn parse_yaffs_obj_header(
    header_data: &[u8],
    endianness: &str,
) -> Result<YAFFSObject, structures::common::StructureError> {
    const UNUSED: usize = 0xFFFF;
    const OBJ_STRUCT_SIZE: usize = 10;

    // First part of an object header
    let yaffs_object_structure = vec![
        ("type", "u32"),
        ("parent_id", "u32"),
        ("name_checksum", "u16"),
    ];

    // Allowed object types
    let allowed_types: Vec<usize> = vec![0, 1, 2, 3, 4, 5];

    if header_data.len() >= OBJ_STRUCT_SIZE {
        let obj_header = structures::common::parse(
            &header_data[0..OBJ_STRUCT_SIZE],
            &yaffs_object_structure,
            endianness,
        );

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

    return Err(structures::common::StructureError);
}

#[derive(Debug, Default, Clone)]
pub struct YAFFSFileHeader {
    // Only this field is needed, for now. Struct may be updated in the future if necessary.
    pub file_size: usize,
}

pub fn parse_yaffs_file_header(
    header_data: &[u8],
    endianness: &str,
) -> Result<YAFFSFileHeader, structures::common::StructureError> {
    const INFO_STRUCT_SIZE: usize = 28;

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

    if header_data.len() >= INFO_STRUCT_SIZE {
        let file_info = structures::common::parse(
            &header_data[0..INFO_STRUCT_SIZE],
            &yaffs_file_info,
            endianness,
        );

        return Ok(YAFFSFileHeader {
            file_size: file_info["file_size"],
        });
    }

    return Err(structures::common::StructureError);
}
