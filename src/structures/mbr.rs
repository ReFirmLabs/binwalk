use crate::structures::common::{self, StructureError};
use std::collections::HashMap;

/// Struct to store MBR partition info
#[derive(Debug, Default, Clone)]
pub struct MBRPartition {
    pub start: usize,
    pub size: usize,
    pub name: String,
}

/// Struct to store MBR info
#[derive(Debug, Default, Clone)]
pub struct MBRHeader {
    pub image_size: usize,
    pub partitions: Vec<MBRPartition>,
}

/// Parse a Master Boot Record image
pub fn parse_mbr_image(mbr_data: &[u8]) -> Result<MBRHeader, StructureError> {
    const BLOCK_SIZE: usize = 512;
    const MIN_IMAGE_SIZE: usize = BLOCK_SIZE * 2;

    const PARTITION_COUNT: usize = 4;
    const PARTITION_TABLE_OFFSET: usize = 446;

    let partition_entry_structure = vec![
        ("status", "u8"),
        ("chs_start", "u24"),
        ("os_type", "u8"),
        ("chs_end", "u24"),
        ("lba_start", "u32"),
        ("lba_size", "u32"),
    ];

    let known_os_types = HashMap::from([
        (0x07, "NTFS_IFS_HPFS_exFAT"),
        (0x0B, "FAT32"),
        (0x0C, "FAT32"),
        (0x43, "Linux"),
        (0x4D, "QNX Primary Volume"),
        (0x4E, "QNX Secondary Volume"),
        (0x81, "Minix"),
        (0x83, "Linux"),
        (0x8E, "Linux LVM"),
        (0x96, "ISO-9660"),
        (0xB1, "QNXv6 File System"),
        (0xB2, "QNXv6 File System"),
        (0xB3, "QNXv6 File System"),
        (0xEE, "EFI GPT Protective"),
        (0xEF, "EFI System Partition"),
    ]);

    let allowed_status_values: Vec<usize> = vec![0, 0x80];
    let partition_structure_size = common::size(&partition_entry_structure);

    let partition_table_start: usize = PARTITION_TABLE_OFFSET;
    let partition_table_end: usize =
        partition_table_start + (partition_structure_size * PARTITION_COUNT);

    let mut mbr_header = MBRHeader {
        ..Default::default()
    };

    // Get the partition table raw bytes
    if let Some(partition_table) = mbr_data.get(partition_table_start..partition_table_end) {
        // Parse each partition table entry
        for i in 0..PARTITION_COUNT {
            // Offset in the partition table for this entry
            let partition_entry_start: usize = i * partition_structure_size;

            // Parse this partition table entry
            match common::parse(
                &partition_table[partition_entry_start..],
                &partition_entry_structure,
                "little",
            ) {
                Err(_) => {
                    return Err(StructureError);
                }
                Ok(partition_entry) => {
                    // OS type of zero or LBA size of 0 can be ignored
                    if partition_entry["os_type"] != 0 || partition_entry["lba_size"] != 0 {
                        // Validate the reported MBR status value
                        if allowed_status_values.contains(&partition_entry["status"]) {
                            // Default to unknown partition type
                            let mut this_partition_name: &str = "Unknown";

                            // If partition type is known, provide a descriptive name
                            if known_os_types.contains_key(&partition_entry["os_type"]) {
                                this_partition_name = known_os_types[&partition_entry["os_type"]];
                            }

                            // Create an MBRPartition structure for this entry
                            let this_partition = MBRPartition {
                                start: partition_entry["lba_start"] * BLOCK_SIZE,
                                size: partition_entry["lba_size"] * BLOCK_SIZE,
                                name: this_partition_name.to_string(),
                            };

                            // Calculate where this partition ends
                            let this_partition_end_offset =
                                this_partition.start + this_partition.size;

                            // Some valid MBRs have partitions that start/end out of bounds WRT the disk image.
                            // Not sure why? At any rate, don't include them in the reported partitions.
                            if this_partition_end_offset <= mbr_data.len() {
                                // Don't report the partition where the MBR header resides
                                if this_partition.start != 0 {
                                    // Add it to the list of partitions
                                    mbr_header.partitions.push(this_partition.clone());
                                }

                                // Image size is the end of the farthest away partition
                                if this_partition_end_offset > mbr_header.image_size {
                                    mbr_header.image_size = this_partition_end_offset;
                                }
                            }
                        }
                    }
                }
            }
        }

        // There should be at least one valid partition
        if !mbr_header.partitions.is_empty() {
            // Total size should be greater than minimum size
            if mbr_header.image_size > MIN_IMAGE_SIZE {
                return Ok(mbr_header);
            }
        }
    }

    Err(StructureError)
}
