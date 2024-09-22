use crate::structures;

// This really just needs to validate the header
pub fn parse_zip_header(zip_data: &[u8]) -> Result<bool, structures::common::StructureError> {
    const ZIP_LOCAL_FILE_HEADER_MIN_SIZE: usize = 30;
    const UNUSED_FLAGS_MASK: usize = 0b11010111_10000000;

    let zip_local_file_structure = vec![
        ("magic", "u32"),
        ("version", "u16"),
        ("flags", "u16"),
        ("compression", "u16"),
        ("modification_time", "u16"),
        ("modification_date", "u16"),
        ("crc", "u32"),
        ("compressed_size", "u32"),
        ("uncompressed_size", "u32"),
        ("file_name_len", "u16"),
        ("extra_field_len", "u16"),
    ];

    let allowed_compression_methods: Vec<usize> = vec![0, 1, 2, 3, 4, 5, 6, 8, 9, 10, 12, 14, 18, 19, 98];

    // Sanity check the size of available data
    if zip_data.len() > ZIP_LOCAL_FILE_HEADER_MIN_SIZE {
        // Calculate the start and end offsets of the ZIP local file structure
        let zip_local_file_start: usize = 0;
        let zip_local_file_end: usize = zip_local_file_start + ZIP_LOCAL_FILE_HEADER_MIN_SIZE;

        // Parse the ZIP local file structure
        let zip_local_file_header = structures::common::parse(&zip_data[zip_local_file_start..zip_local_file_end], &zip_local_file_structure, "little");

        // Unused/reserved flag bits should be 0
        if (zip_local_file_header["flags"] & UNUSED_FLAGS_MASK) == 0 {
            // Specified compression method should be one of the defined ZIP compression methods
            if allowed_compression_methods.contains(&zip_local_file_header["compression"]) {
                return Ok(true);
            }
        }
    }

    return Err(structures::common::StructureError);
}

#[derive(Debug, Default, Clone)]
pub struct ZipEOCDHeader {
    pub size: usize,
    pub file_count: usize,
}

pub fn parse_eocd_header(eocd_data: &[u8]) -> Result<ZipEOCDHeader, structures::common::StructureError> {
    // Minimum size of the EOCD header
    const ZIP_EOCD_HEADER_MIN_SIZE: usize = 22;

    let zip_eocd_structure = vec![
        ("magic", "u32"),
        ("disk_number", "u16"),
        ("central_directory_disk_number", "u16"),
        ("central_directory_disk_entries", "u16"),
        ("central_directory_total_entries", "u16"),
        ("central_directory_size", "u32"),
        ("central_directory_offset", "u32"),
        ("comment_length", "u16"),
    ];

    // Calculate the start and end of the fixed-size portion of the ZIP EOCD header in the file data
    let eocd_start: usize = 0;
    let eocd_end: usize = eocd_start + ZIP_EOCD_HEADER_MIN_SIZE;

    // Sanity check that there is enough data in the file to process this potential EOCD record
    if eocd_data.len() >= eocd_end {
        // Parse the EOCD header
        let zip_eocd_header = structures::common::parse(&eocd_data[eocd_start..eocd_end], &zip_eocd_structure, "little");

        // Assume there is only one "disk", so disk entries and total entries should be the same, and the ZIP archive should contain at least one file
        if zip_eocd_header["central_directory_disk_entries"] == zip_eocd_header["central_directory_total_entries"] && zip_eocd_header["central_directory_total_entries"] > 0 {
            // An optional comment may follow the EOCD header; include the comment length in the offset of the ZIP EOF
            let zip_eof: usize = eocd_end + zip_eocd_header["comment_length"];

            return Ok(ZipEOCDHeader {
                size: zip_eof,
                file_count: zip_eocd_header["central_directory_total_entries"],
            });
        }
    }

    return Err(structures::common::StructureError);
}
