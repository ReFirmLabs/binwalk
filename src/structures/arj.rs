use crate::common::{epoch_to_string, get_cstring};
use crate::structures::common;
use crate::structures::common::StructureError;

#[derive(Debug, Default, Clone)]
pub struct ARJHeader {
    pub header_size: usize,
    pub version: u8,
    pub min_version: u8,
    pub flags: String,
    pub host_os: String,
    pub compression_method: String,
    pub file_type: String,
    pub original_name: String,
    pub original_file_date: String,
    pub compressed_file_size: i32,
    pub uncompressed_file_size: i32,
}

pub fn parse_arj_header(arj_data: &[u8]) -> Result<ARJHeader, StructureError> {
    // ARJ header structure (https://www.fileformat.info/format/arj/corion.htm)
    let arj_header_structure = vec![
        ("magic", "u16"),               // offset 0x00
        ("basic_header_size", "u16"),   // offset 0x02
        ("extra_header_size", "u8"),    // offset 0x04
        ("archiver_version", "u8"),     // offset 0x05
        ("min_version", "u8"),          // offset 0x06
        ("host_os", "u8"),              // offset 0x07
        ("internal_flags", "u8"),       // offset 0x08
        ("compression_method", "u8"),   // offset 0x09
        ("file_type", "u8"),            // offset 0x0A
        ("reserved1", "u8"),            // offset 0x0B
        ("datetime_file", "u32"),       // offset 0x0C
        ("compressed_filesize", "u32"), // offset 0x10
        ("original_filesize", "u32"),   // offset 0x14
    ];

    if let Ok(arj_header) = common::parse(arj_data, &arj_header_structure, "little") {
        // check the version information in the header
        if !(1..=16).contains(&arj_header["archiver_version"])
            || !(1..=16).contains(&arj_header["min_version"])
            || arj_header["archiver_version"] < arj_header["min_version"]
        {
            return Err(StructureError);
        }
        let mut flags = if arj_header["internal_flags"] & 0x01 != 0 {
            "password".to_string()
        } else {
            "no password".to_string()
        };
        if arj_header["internal_flags"] & 0x04 != 0 {
            flags = format!("{flags}|multi-volume");
        }
        // let file_start_pos_is_available =  arj_header["internal_flags"] & 0x08 != 0;
        if arj_header["internal_flags"] & 0x10 != 0 {
            flags = format!("{flags}|slash-switched");
        }
        if arj_header["internal_flags"] & 0x20 != 0 {
            flags = format!("{flags}|backup");
        }
        let host_os = match &arj_header["host_os"] {
            0 => "MS-DOS".to_string(),
            1 => "PRIMOS".to_string(),
            2 => "UNIX".to_string(),
            3 => "AMIGA".to_string(),
            4 => "MAX-OS".to_string(),
            5 => "OS/2".to_string(),
            6 => "APPLE GS".to_string(),
            7 => "ATARI ST".to_string(),
            8 => "NeXT".to_string(),
            9 => "VAX VMS".to_string(),
            _ => return Err(StructureError),
        };
        let compression_method = match &arj_header["compression_method"] {
            0 => "stored".to_string(),
            1 => "compressed most".to_string(),
            2 => "compressed".to_string(),
            3 => "compressed faster".to_string(),
            4 => "compressed fastest".to_string(),
            _ => return Err(StructureError),
        };
        let file_type = match &arj_header["file_type"] {
            0 => "binary".to_string(),
            1 => "7-bit text".to_string(),
            2 => "comment header".to_string(),
            3 => "directory".to_string(),
            4 => "volume label".to_string(),
            _ => return Err(StructureError),
        };
        let compressed_file_size = arj_header["compressed_filesize"] as i32;
        if compressed_file_size < 0 {
            return Err(StructureError);
        }
        let uncompressed_file_size = arj_header["original_filesize"] as i32;
        if uncompressed_file_size < 0 {
            return Err(StructureError);
        }

        let header_size = arj_header["extra_header_size"];
        let original_name = if let Some(data) = arj_data.get(header_size + 4..) {
            get_cstring(data)
        } else {
            "".to_string()
        };

        return Ok(ARJHeader {
            header_size,
            version: arj_header["archiver_version"] as u8,
            min_version: arj_header["min_version"] as u8,
            flags,
            host_os,
            compression_method,
            file_type,
            original_name,
            original_file_date: epoch_to_string(arj_header["datetime_file"] as u32),
            compressed_file_size,
            uncompressed_file_size,
        });
    }

    Err(StructureError)
}
