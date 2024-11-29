use crate::structures::common::{self, StructureError};

/// Struct to store Android boot image header info
#[derive(Debug, Default, Clone)]
pub struct AndroidBootImageHeader {
    pub kernel_size: usize,
    pub ramdisk_size: usize,
    pub kernel_load_address: usize,
    pub ramdisk_load_address: usize,
}

/// Parses an Android boot image header
pub fn parse_android_bootimg_header(
    bootimg_data: &[u8],
) -> Result<AndroidBootImageHeader, StructureError> {
    let bootimg_structure = vec![
        ("magic", "u64"),
        ("kernel_size", "u32"),
        ("kernel_load_addr", "u32"),
        ("ramdisk_size", "u32"),
        ("ramdisk_load_addr", "u32"),
    ];

    // Parse the header
    if let Ok(bootimg_header) = common::parse(bootimg_data, &bootimg_structure, "little") {
        return Ok(AndroidBootImageHeader {
            kernel_size: bootimg_header["kernel_size"],
            kernel_load_address: bootimg_header["kernel_load_addr"],
            ramdisk_size: bootimg_header["ramdisk_size"],
            ramdisk_load_address: bootimg_header["ramdisk_load_addr"],
        });
    }

    Err(StructureError)
}
