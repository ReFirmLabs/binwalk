use crate::structures::common::{self, StructureError};

/// Stores TRX firmware header info
#[derive(Debug, Clone, Default)]
pub struct TRXHeader {
    pub version: usize,
    pub checksum: usize,
    pub total_size: usize,
    pub header_size: usize,
    pub partitions: Vec<usize>,
}

/// Parse a TRX firmware header
pub fn parse_trx_header(header_data: &[u8]) -> Result<TRXHeader, StructureError> {
    // TRX comes in two flavors: v1 and v2
    const TRX_VERSION_2: usize = 2;

    let trx_header_structure = vec![
        ("magic", "u32"),
        ("total_size", "u32"),
        ("crc32", "u32"),
        ("flags", "u16"),
        ("version", "u16"),
        ("partition1_offset", "u32"),
        ("partition2_offset", "u32"),
        ("partition3_offset", "u32"),
        ("partition4_offset", "u32"),
    ];

    let allowed_versions: Vec<usize> = vec![1, 2];

    // Size of the fixed-length portion of the header structure
    let mut struct_size: usize = common::size(&trx_header_structure);

    // Parse the header
    if let Ok(trx_header) = common::parse(header_data, &trx_header_structure, "little") {
        // Sanity check partition offsets. Partition offsets may be 0.
        if trx_header["partition1_offset"] <= trx_header["total_size"]
            && trx_header["partition2_offset"] <= trx_header["total_size"]
            && trx_header["partition3_offset"] <= trx_header["total_size"]
        {
            // Sanity check the reported total size
            if trx_header["total_size"] > struct_size {
                // Sanity check the reported version number
                if allowed_versions.contains(&trx_header["version"]) {
                    let mut partitions: Vec<usize> = vec![];

                    if trx_header["partition1_offset"] != 0 {
                        partitions.push(trx_header["partition1_offset"]);
                    }

                    if trx_header["partition2_offset"] != 0 {
                        partitions.push(trx_header["partition2_offset"]);
                    }

                    if trx_header["partition3_offset"] != 0 {
                        partitions.push(trx_header["partition3_offset"]);
                    }

                    // Only TRXv2 has a fourth partition entry
                    if trx_header["version"] == TRX_VERSION_2 {
                        if trx_header["partition4_offset"] != 0 {
                            partitions.push(trx_header["partition4_offset"]);
                        }
                    } else {
                        // For TRXv1, this means the real structure size is 4 bytes shorter
                        struct_size -= std::mem::size_of::<u32>();
                    }

                    return Ok(TRXHeader {
                        version: trx_header["version"],
                        checksum: trx_header["crc32"],
                        total_size: trx_header["total_size"],
                        header_size: struct_size,
                        partitions: partitions.clone(),
                    });
                }
            }
        }
    }

    Err(StructureError)
}
