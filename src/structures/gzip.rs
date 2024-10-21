use crate::common::get_cstring;
use crate::structures::common::{self, StructureError};
use std::collections::HashMap;

/// Struct to store useful Gzip header info
#[derive(Debug, Clone, Default)]
pub struct GzipHeader {
    pub os: String,
    pub size: usize,
    pub comment: String,
    pub timestamp: u32,
    pub original_name: String,
}

/// Parses a Gzip file header
pub fn parse_gzip_header(header_data: &[u8]) -> Result<GzipHeader, StructureError> {
    // Some expected constant values
    const CRC_SIZE: usize = 2;
    const NULL_BYTE_SIZE: usize = 1;
    const DEFLATE_COMPRESSION: usize = 8;

    const FLAG_CRC: usize = 0b0000_0010;
    const FLAG_EXTRA: usize = 0b0000_0100;
    const FLAG_NAME: usize = 0b0000_1000;
    const FLAG_COMMENT: usize = 0b0001_0000;
    const FLAG_RESERVED: usize = 0b1110_0000;

    let gzip_header_structure = vec![
        ("magic", "u16"),
        ("compression_method", "u8"),
        ("flags", "u8"),
        ("timestamp", "u32"),
        ("extra_flags", "u8"),
        ("osid", "u8"),
    ];

    let gzip_extra_header_structure = vec![("id", "u16"), ("extra_data_len", "u16")];

    let known_os_ids: HashMap<usize, &str> = HashMap::from([
        (0, "FAT filesystem (MS-DOS, OS/2, NT/Win32"),
        (1, "Amiga"),
        (2, "VMS (or OpenVMS)"),
        (3, "Unix"),
        (4, "VM/CMS"),
        (5, "Atari TOS"),
        (6, "HPFS filesystem (OS/2, NT)"),
        (7, "Macintosh"),
        (8, "Z-System"),
        (9, "CP/M"),
        (10, "TOPS-20"),
        (11, "NTFS filesystem (NT)"),
        (12, "QDOS"),
        (13, "Acorn RISCOS"),
        (255, "unknown"),
    ]);

    let mut header_info = GzipHeader {
        ..Default::default()
    };

    // End of the fixed-size portion of the gzip header
    header_info.size = common::size(&gzip_header_structure);

    // Parse the gzip header
    if let Ok(gzip_header) = common::parse(header_data, &gzip_header_structure, "little") {
        // Report the timestamp
        header_info.timestamp = gzip_header["timestamp"] as u32;

        // Sanity check; compression type should be deflate, reserved flag bits should not be set, OS ID should be a known value
        if (gzip_header["flags"] & FLAG_RESERVED) == 0
            && gzip_header["compression_method"] == DEFLATE_COMPRESSION
            && known_os_ids.contains_key(&gzip_header["osid"])
        {
            // Set the operating system string
            header_info.os = known_os_ids[&gzip_header["osid"]].to_string();

            // Check if the optional "extra" data follows the standard Gzip header
            if (gzip_header["flags"] & FLAG_EXTRA) != 0 {
                // File offsets and sizes for parsing the extra header
                let extra_header_size = common::size(&gzip_extra_header_structure);
                let extra_header_start: usize = header_info.size;
                let extra_header_end: usize = extra_header_start + extra_header_size;

                match header_data.get(extra_header_start..extra_header_end) {
                    None => {
                        return Err(StructureError);
                    }
                    Some(extra_header_data) => {
                        // Parse the extra header and update the header_info.size to include this data
                        match common::parse(
                            extra_header_data,
                            &gzip_extra_header_structure,
                            "little",
                        ) {
                            Err(e) => {
                                return Err(e);
                            }
                            Ok(extra_header) => {
                                header_info.size +=
                                    extra_header_size + extra_header["extra_data_len"];
                            }
                        }
                    }
                }
            }

            // If the NULL-terminated original file name is included, it will be next
            if (gzip_header["flags"] & FLAG_NAME) != 0 {
                match header_data.get(header_info.size..) {
                    None => {
                        return Err(StructureError);
                    }
                    Some(file_name_bytes) => {
                        header_info.original_name = get_cstring(file_name_bytes);
                        // The value returned by get_cstring does not include the terminating NULL byte
                        header_info.size += header_info.original_name.len() + NULL_BYTE_SIZE;
                    }
                }
            }

            // If a NULL-terminated comment is included, it will be next
            if (gzip_header["flags"] & FLAG_COMMENT) != 0 {
                match header_data.get(header_info.size..) {
                    None => {
                        return Err(StructureError);
                    }
                    Some(comment_bytes) => {
                        header_info.comment = get_cstring(comment_bytes);
                        // The value returned by get_cstring does not include the terminating NULL byte
                        header_info.size += header_info.comment.len() + NULL_BYTE_SIZE;
                    }
                }
            }

            // Finally, a checksum field may be included
            if (gzip_header["flags"] & FLAG_CRC) != 0 {
                header_info.size += CRC_SIZE;
            }

            // Deflate data should start at header_info.size; make sure this offset is sane
            if header_data.len() >= header_info.size {
                return Ok(header_info);
            }
        }
    }

    Err(StructureError)
}
