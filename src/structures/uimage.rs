use crate::common::{crc32, get_cstring};
use crate::structures::common::{self, StructureError};
use std::collections::HashMap;

/// Stores info about a uImage header
#[derive(Debug, Default, Clone)]
pub struct UImageHeader {
    pub header_size: usize,
    pub name: String,
    pub data_size: usize,
    pub data_checksum: usize,
    pub load_address: usize,
    pub entry_point_address: usize,
    pub timestamp: usize,
    pub compression_type: String,
    pub cpu_type: String,
    pub os_type: String,
    pub image_type: String,
}

/// Pase a uImage header
pub fn parse_uimage_header(uimage_data: &[u8]) -> Result<UImageHeader, StructureError> {
    const UIMAGE_HEADER_SIZE: usize = 64;
    const UIMAGE_NAME_OFFSET: usize = 32;

    let uimage_structure = vec![
        ("magic", "u32"),
        ("header_crc", "u32"),
        ("creation_timestamp", "u32"),
        ("data_size", "u32"),
        ("load_address", "u32"),
        ("entry_point_address", "u32"),
        ("data_crc", "u32"),
        ("os_type", "u8"),
        ("cpu_type", "u8"),
        ("image_type", "u8"),
        ("compression_type", "u8"),
    ];

    let valid_os_types = HashMap::from([
        (1, "OpenBSD"),
        (2, "NetBSD"),
        (3, "FreeBSD"),
        (4, "4.4BSD"),
        (5, "Linux"),
        (6, "SVR4"),
        (7, "Esix"),
        (8, "Solaris"),
        (9, "Irix"),
        (10, "SCO"),
        (11, "Dell"),
        (12, "NCR"),
        (13, "LynxOS"),
        (14, "VxWorks"),
        (15, "pSOS"),
        (16, "QNX"),
        (17, "Firmware"),
        (18, "RTEMS"),
        (19, "ARTOS"),
        (20, "Unity OS"),
        (21, "INTEGRITY"),
        (22, "OSE"),
        (23, "Plan 9"),
        (24, "OpenRTOS"),
        (25, "ARM Trusted Firmware"),
        (26, "Trusted Execution Environment"),
        (27, "OpenSBI"),
        (28, "EFI Firmware"),
        (29, "ELF Image"),
    ]);

    let valid_cpu_types = HashMap::from([
        (1, "Alpha"),
        (2, "ARM"),
        (3, "Intel x86"),
        (4, "IA64"),
        (5, "MIPS32"),
        (6, "MIPS64"),
        (7, "PowerPC"),
        (8, "IBM S390"),
        (10, "SuperH"),
        (11, "Sparc"),
        (12, "Sparc64"),
        (13, "M68K"),
        (14, "Nios-32"),
        (15, "MicroBlaze"),
        (16, "Nios-II"),
        (17, "Blackfin"),
        (18, "AVR32"),
        (19, "ST200"),
        (20, "Sandbox"),
        (21, "NDS32"),
        (22, "OpenRISC"),
        (23, "ARM64"),
        (24, "ARC"),
        (25, "x86-64"),
        (26, "Xtensa"),
        (27, "RISC-V"),
    ]);

    let valid_compression_types = HashMap::from([
        (0, "none"),
        (1, "gzip"),
        (2, "bzip2"),
        (3, "lzma"),
        (4, "lzo"),
        (5, "lz4"),
        (6, "zstd"),
    ]);

    let valid_image_types = HashMap::from([
        (1, "Standalone Program"),
        (2, "OS Kernel Image"),
        (3, "RAMDisk Image"),
        (4, "Multi-File Image"),
        (5, "Firmware Image"),
        (6, "Script file"),
        (7, "Filesystem Image"),
        (8, "Binary Flat Device Tree Blob"),
        (9, "Kirkwood Boot Image"),
        (10, "Freescale IMXBoot Image"),
        (11, "Davinci UBL Image"),
        (12, "TI OMAP Config Header Image"),
        (13, "TI Davinci AIS Image"),
        (14, "OS Kernel Image"),
        (15, "Freescale PBL Boot Image"),
        (16, "Freescale MXSBoot Image"),
        (17, "TI Keystone GPHeader Image"),
        (18, "ATMEL ROM bootable Image"),
        (19, "Altera SOCFPGA CV/AV Preloader"),
        (20, "x86 setup.bin Image"),
        (21, "x86 setup.bin Image"),
        (22, "A list of typeless images"),
        (23, "Rockchip Boot Image"),
        (24, "Rockchip SD card"),
        (25, "Rockchip SPI image"),
        (26, "Xilinx Zynq Boot Image"),
        (27, "Xilinx ZynqMP Boot Image"),
        (28, "Xilinx ZynqMP Boot Image (bif)"),
        (29, "FPGA Image"),
        (30, "VYBRID .vyb Image"),
        (31, "Trusted Execution Environment OS Image"),
        (32, "Firmware Image with HABv4 IVT"),
        (33, "TI Power Management Micro-Controller Firmware"),
        (34, "STMicroelectronics STM32 Image"),
        (35, "Altera SOCFPGA A10 Preloader"),
        (36, "MediaTek BootROM loadable Image"),
        (37, "Freescale IMX8MBoot Image"),
        (38, "Freescale IMX8Boot Image"),
        (39, "Coprocessor Image for remoteproc"),
        (40, "Allwinner eGON Boot Image"),
        (41, "Allwinner TOC0 Boot Image"),
        (42, "Binary Flat Device Tree Blob in a Legacy Image"),
        (43, "Renesas SPKG image"),
        (44, "StarFive SPL image"),
    ]);

    // Parse the first half of the header
    if let Ok(uimage_header) = common::parse(uimage_data, &uimage_structure, "big") {
        // Sanity check header fields
        if valid_os_types.contains_key(&uimage_header["os_type"])
            && valid_cpu_types.contains_key(&uimage_header["cpu_type"])
            && valid_image_types.contains_key(&uimage_header["image_type"])
            && valid_compression_types.contains_key(&uimage_header["compression_type"])
        {
            // Finally, validate the header CRC
            if let Some(crc_data) = uimage_data.get(0..UIMAGE_HEADER_SIZE) {
                if calculate_uimage_header_checksum(crc_data) == uimage_header["header_crc"] {
                    return Ok(UImageHeader {
                        header_size: UIMAGE_HEADER_SIZE,
                        name: get_cstring(&uimage_data[UIMAGE_NAME_OFFSET..]),
                        data_size: uimage_header["data_size"],
                        data_checksum: uimage_header["data_crc"],
                        timestamp: uimage_header["creation_timestamp"],
                        load_address: uimage_header["load_address"],
                        entry_point_address: uimage_header["entry_point_address"],
                        compression_type: valid_compression_types
                            [&uimage_header["compression_type"]]
                            .to_string(),
                        cpu_type: valid_cpu_types[&uimage_header["cpu_type"]].to_string(),
                        os_type: valid_os_types[&uimage_header["os_type"]].to_string(),
                        image_type: valid_image_types[&uimage_header["image_type"]].to_string(),
                    });
                }
            }
        }
    }

    Err(StructureError)
}

/// uImage checksum calculator
fn calculate_uimage_header_checksum(hdr: &[u8]) -> usize {
    const HEADER_CRC_START: usize = 4;
    const HEADER_CRC_END: usize = 8;

    // Header checksum has to be nulled out to calculate the CRC
    let mut uimage_header: Vec<u8> = hdr.to_vec();

    for crc_byte in uimage_header
        .iter_mut()
        .take(HEADER_CRC_END)
        .skip(HEADER_CRC_START)
    {
        *crc_byte = 0;
    }

    crc32(&uimage_header) as usize
}
