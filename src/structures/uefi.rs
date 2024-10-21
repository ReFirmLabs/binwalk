use crate::structures::common::{self, StructureError};

/// Stores info about a UEFI volume header
#[derive(Debug, Default, Clone)]
pub struct UEFIVolumeHeader {
    pub header_crc: usize,
    pub header_size: usize,
    pub volume_size: usize,
}

/// Parse a UEFI volume header
pub fn parse_uefi_volume_header(uefi_data: &[u8]) -> Result<UEFIVolumeHeader, StructureError> {
    // The revision field must be 2
    const EXPECTED_REVISION: usize = 2;

    let uefi_pi_header_structure = vec![
        ("volume_size", "u64"),
        ("magic", "u32"),
        ("attributes", "u32"),
        ("header_size", "u16"),
        ("header_crc", "u16"),
        ("extended_header_offset", "u16"),
        ("reserved", "u8"),
        ("revision", "u8"),
    ];

    // Parse the volume header
    if let Ok(uefi_volume_header) = common::parse(uefi_data, &uefi_pi_header_structure, "little") {
        // Make sure the header size is sane (must be smaller than the total volume size)
        if uefi_volume_header["header_size"] < uefi_volume_header["volume_size"] {
            // The reserved field *must* be 0
            if uefi_volume_header["reserved"] == 0 {
                // The revision number must be 2
                if uefi_volume_header["revision"] == EXPECTED_REVISION {
                    return Ok(UEFIVolumeHeader {
                        // TODO: Validate UEFI header CRC
                        header_crc: uefi_volume_header["header_crc"],
                        header_size: uefi_volume_header["header_size"],
                        volume_size: uefi_volume_header["volume_size"],
                    });
                }
            }
        }
    }

    Err(StructureError)
}

/// Stores info about a UEFI capsule header
#[derive(Debug, Default, Clone)]
pub struct UEFICapsuleHeader {
    pub total_size: usize,
    pub header_size: usize,
}

/// Parse  UEFI capsule header
pub fn parse_uefi_capsule_header(uefi_data: &[u8]) -> Result<UEFICapsuleHeader, StructureError> {
    let uefi_capsule_structure = vec![
        ("guid_p1", "u64"),
        ("guid_p2", "u64"),
        ("header_size", "u32"),
        ("flags", "u32"),
        ("total_size", "u32"),
    ];

    // Parse the capsule header
    if let Ok(capsule_header) = common::parse(uefi_data, &uefi_capsule_structure, "little") {
        // Sanity check on header and total size fields
        if capsule_header["header_size"] < capsule_header["total_size"] {
            return Ok(UEFICapsuleHeader {
                total_size: capsule_header["total_size"],
                header_size: capsule_header["header_size"],
            });
        }
    }

    Err(StructureError)
}
