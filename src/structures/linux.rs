use crate::structures::common::{self, StructureError};

/// Struct to store linux ARM64 boot image header info
#[derive(Debug, Default, Clone)]
pub struct LinuxARM64BootHeader {
    pub header_size: usize,
    pub image_size: usize,
    pub endianness: String,
}

/// Parses a linux ARM64 boot header
pub fn parse_linux_arm64_boot_image_header(
    img_data: &[u8],
) -> Result<LinuxARM64BootHeader, StructureError> {
    const PE: &[u8] = b"PE";
    const FLAGS_RESERVED_MASK: usize =
        0b11111111_11111111_11111111_11111111_11111111_11111111_11111111_11110000;
    const FLAGS_ENDIAN_MASK: usize = 1;
    const BIG_ENDIAN: usize = 1;

    // https://www.kernel.org/doc/Documentation/arm64/booting.txt
    let boot_img_structure = vec![
        ("code0", "u32"),
        ("code1", "u32"),
        ("image_load_offset", "u64"),
        ("image_size", "u64"),
        ("flags", "u64"),
        ("reserved1", "u64"),
        ("reserved2", "u64"),
        ("reserved3", "u64"),
        ("magic", "u32"),
        ("pe_offset", "u32"),
    ];

    let mut result = LinuxARM64BootHeader {
        ..Default::default()
    };

    // Parse the header
    if let Ok(img_header) = common::parse(img_data, &boot_img_structure, "little") {
        // Make sure the reserved fields are not set
        if img_header["reserved1"] == 0
            && img_header["reserved2"] == 0
            && img_header["reserved3"] == 0
        {
            // Start and end of PE signature
            let pe_start = img_header["pe_offset"];
            let pe_end = pe_start + PE.len();

            // Get the data pointed to by the pe_offset header field
            if let Some(pe_data) = img_data.get(pe_start..pe_end) {
                // There should be a PE header here
                if pe_data == PE {
                    // Make sure the reserved flag bits are not set
                    if (img_header["flags"] & FLAGS_RESERVED_MASK) == 0 {
                        // Determine the endianness from the flags field
                        if (img_header["flags"] & FLAGS_ENDIAN_MASK) == BIG_ENDIAN {
                            result.endianness = "big".to_string();
                        } else {
                            result.endianness = "little".to_string();
                        }

                        // Report the kernel image and header sizes
                        result.image_size = img_header["image_size"];
                        result.header_size = common::size(&boot_img_structure);

                        return Ok(result);
                    }
                }
            }
        }
    }

    Err(StructureError)
}
