use crate::structures::common::{self, StructureError};

/// Struct to store FAT header info
#[derive(Debug, Default, Clone)]
pub struct FATHeader {
    pub is_fat32: bool,
    pub total_size: usize,
}

/// Parses a FAT header
pub fn parse_fat_header(fat_data: &[u8]) -> Result<FATHeader, StructureError> {
    // Number of FATs could technically be 1 or greater, but *should* be 2
    const EXPECTED_FAT_COUNT: usize = 2;

    // http://elm-chan.org/docs/fat_e.html
    let fat_boot_sector_structure = vec![
        ("opcode1", "u8"),
        ("opcode2", "u8"),
        ("opcode3", "u8"),
        ("oem_name", "u64"),
        ("bytes_per_sector", "u16"),
        ("sectors_per_cluster", "u8"),
        ("reserved_sectors", "u16"),
        ("fat_count", "u8"),
        ("root_entries_count_16", "u16"),
        ("total_sectors_16", "u16"),
        ("media_type", "u8"),
        ("fat_size_16", "u16"),
        ("sectors_per_track", "u16"),
        ("number_of_heads", "u16"),
        ("hidden_sectors", "u32"),
        ("total_sectors_32", "u32"),
    ];

    // First opcode should be jump instruction, either EB or E9
    let valid_opcode1: Vec<usize> = vec![0xEB, 0xE9];

    // bytes_per_sector must be one of these values
    let valid_sector_sizes: Vec<usize> = vec![512, 1024, 2048, 4096];

    // sectors_per_cluster must be one of these values
    let valid_sectors_per_cluster: Vec<usize> = vec![1, 2, 4, 8, 16, 32, 64, 128];

    // media_type must be one of these values
    let valid_media_types: Vec<usize> = vec![0xF0, 0xF8, 0xF9, 0xFA, 0xFB, 0xFC, 0xFD, 0xFE];

    // Return value
    let mut result = FATHeader {
        ..Default::default()
    };

    // Parse the boot sector header
    if let Ok(bs_header) = common::parse(fat_data, &fat_boot_sector_structure, "little") {
        // Sanity check the first opcode
        if valid_opcode1.contains(&bs_header["opcode1"]) {
            // Sanity check the reported sector size
            if valid_sector_sizes.contains(&bs_header["bytes_per_sector"]) {
                // Sanity check the reported sectors per cluster
                if valid_sectors_per_cluster.contains(&bs_header["sectors_per_cluster"]) {
                    // Reserved sectors must be at least 1
                    if bs_header["reserved_sectors"] > 0 {
                        // Sanity check the reported number of FATs
                        if bs_header["fat_count"] == EXPECTED_FAT_COUNT {
                            // Sanity check the reported media type
                            if valid_media_types.contains(&bs_header["media_type"]) {
                                // This field is set to 0 for FAT32, but populated by FAT12/16
                                result.is_fat32 = bs_header["fat_size_16"] == 0;

                                // total_sectors_16 is used for FAT12/16 that have less than 0x10000 sectors
                                if bs_header["total_sectors_16"] != 0 {
                                    result.total_size = bs_header["total_sectors_16"]
                                        * bs_header["bytes_per_sector"];
                                // Else, total_sectors_32 is used to define the number of sectors
                                } else {
                                    result.total_size = bs_header["total_sectors_32"]
                                        * bs_header["bytes_per_sector"];
                                }

                                // If both total_sectors_32 and total_sectors_16 is 0, this is not a valid FAT
                                if result.total_size > 0 {
                                    return Ok(result);
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    Err(StructureError)
}
