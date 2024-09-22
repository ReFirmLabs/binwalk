use crate::structures;

#[derive(Debug, Clone, Default)]
pub struct TRXHeader {
    pub version: usize,
    pub total_size: usize,
    pub header_size: usize,
    pub boot_partition: usize,
    pub kernel_partition: usize,
    pub rootfs_partition: usize,
}

pub fn parse_trx_header(header_data: &[u8]) -> Result<TRXHeader, structures::common::StructureError> {

    let trx_header_structure = vec![
        ("magic", "u32"),
        ("total_size", "u32"),
        ("crc32", "u32"),
        ("flags", "u16"),
        ("version", "u16"),
        ("boot_partition_offset", "u32"),
        ("kernel_partition_offset", "u32"),
        ("rootfs_partition_offset", "u32"),
    ];

    // Size of the fixed-length portion of the header structure
    let struct_size: usize = structures::common::size(&trx_header_structure);

    // Sanity check the available data
    if header_data.len() > struct_size {

        // Parse the header
        let trx_header = structures::common::parse(&header_data[0..struct_size], &trx_header_structure, "little");

        // Sanity check partition offsets. Partition offsets may be 0.
        if trx_header["boot_partition_offset"] <= trx_header["total_size"] &&
           trx_header["kernel_partition_offset"] <= trx_header["total_size"] &&
           trx_header["rootfs_partition_offset"] <= trx_header["total_size"] {
       
            // Sanity check the reported total size
            if trx_header["total_size"] > struct_size {

                return Ok(TRXHeader {
                    version: trx_header["version"],
                    total_size: trx_header["total_size"],
                    header_size: struct_size,
                    boot_partition: trx_header["boot_partition_offset"],
                    kernel_partition: trx_header["kernel_partition_offset"],
                    rootfs_partition: trx_header["rootfs_partition_offset"],
                });
            }
        }
    }

    return Err(structures::common::StructureError);
}
