use crate::structures::common::{self, StructureError};

/// TIFF magic bytes
const TIFF_MAGIC_LE: u16 = 0x4949; // "II" (little-endian)
const TIFF_MAGIC_BE: u16 = 0x4D4D; // "MM" (big-endian)
const TIFF_VERSION: u16 = 42;

/// Parse and validate a TIFF file header
pub fn get_tiff_size(tiff_data: &[u8]) -> Result<usize, StructureError> {
    let tiff_header_structure = vec![
        ("identifier", "u16"),      // 0x4949 for little-endian, 0x4D4D for big-endian
        ("version", "u16"),         // Should be 42
        ("ifd_offset", "u32"),      // Offset to first Image File Directory (IFD)
    ];

    // Try parsing
    if tiff_data.len() >= common::size(&tiff_header_structure) {
        let identifier = u16::from_le_bytes(tiff_data[..2].try_into().unwrap());
        if identifier != TIFF_MAGIC_LE && identifier != TIFF_MAGIC_BE {
            return Err(StructureError);
        }
        let endian = if identifier == TIFF_MAGIC_LE { "little" } else { "big" };
        if let Ok(tiff_header) = common::parse(tiff_data, &tiff_header_structure, endian) {
            if tiff_header["version"] as u16 != TIFF_VERSION {
                return Err(StructureError);
            }
            let ifd_offset = tiff_header["ifd_offset"];
            if let Some(size) = calculate_tiff_size(tiff_data, ifd_offset, endian) {
                return Ok(size);
            }
        }
    }

    Err(StructureError)
}

/// Calculate the total size of a TIFF file by parsing IFDs
fn calculate_tiff_size(tiff_data: &[u8], first_ifd_offset: usize, endian: &str) -> Option<usize> {
    let mut max_offset = first_ifd_offset;
    let mut current_ifd_offset = first_ifd_offset;

    // Follow the IFD chain
    while current_ifd_offset > 0 && current_ifd_offset < tiff_data.len() {
        let ifd_data = &tiff_data.get(current_ifd_offset..)?;

        let ifd_count_struct = vec![("num_dir_entries", "u16")];
        // Parse number of directory entries
        let ifd_count = common::parse(ifd_data, &ifd_count_struct, endian).ok()?;
        let num_entries = ifd_count["num_dir_entries"];

        let tag_structure = vec![
            ("tag_id", "u16"),
            ("data_type", "u16"),
            ("data_count", "u32"),
            ("data_offset", "u32"),
        ];
        // Parse each tag entry
        for i in 0..num_entries {
            let entry_offset = common::size(&ifd_count_struct) + (i * common::size(&tag_structure));
            let tag_data = ifd_data.get(entry_offset..entry_offset + common::size(&tag_structure))?;
            let tag = common::parse(tag_data, &tag_structure, endian).ok()?;

            // Calculate size of the data referenced by this tag
            let data_type_size = match tag["data_type"] {
                1 | 2 | 6 | 7 => 1,    // BYTE, ASCII, SBYTE, UNDEFINED
                3 | 8 => 2,            // SHORT, SSHORT
                4 | 9 | 11 => 4,       // LONG, SLONG, FLOAT
                5 | 10 | 12 => 8,      // RATIONAL, SRATIONAL, DOUBLE
                _ => 0,
            };
            let data_size = data_type_size * tag["data_count"];
            // Update max_offset if data is stored out-of-line
            if data_size > 4 {
                let data_offset = tag["data_offset"];
                max_offset = max_offset.max(data_offset + data_size);
            }
        }
        // Calculate offset to next IFD pointer (after all entries)
        let next_ifd_offset_pos = common::size(&ifd_count_struct) + (num_entries * common::size(&tag_structure));
        // Get next IFD offset
        let next_ifd_offset_data = ifd_data.get(next_ifd_offset_pos..)?;
        let next_ifd_struct = vec![("next_ifd_offset", "u32")];
        let next_ifd = common::parse(next_ifd_offset_data, &next_ifd_struct, endian).ok()?;
        let ifd_size = next_ifd_offset_pos + common::size(&next_ifd_struct);

        max_offset = max_offset.max(current_ifd_offset + ifd_size);
        current_ifd_offset = next_ifd["next_ifd_offset"];
    }

    // Return the end of the last valid data
    Some(max_offset)
}