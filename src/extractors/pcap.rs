use crate::common::is_offset_safe;
use crate::extractors::common::{Chroot, ExtractionResult, Extractor, ExtractorType};
use crate::structures::pcap::{parse_pcapng_block, parse_pcapng_section_block};

/// Defines the internal extractor function for extracting pcap-ng files
pub fn pcapng_extractor() -> Extractor {
    Extractor {
        do_not_recurse: true,
        utility: ExtractorType::Internal(pcapng_carver),
        ..Default::default()
    }
}

/// Carves a pcap-ng file to disk
pub fn pcapng_carver(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&String>,
) -> ExtractionResult {
    // Output file name
    const OUTPUT_FILE_NAME: &str = "capture.pcapng";

    // Pcap-NG files must have at least two blocks: a section header block and an interface description block
    const MIN_BLOCK_COUNT: usize = 2;

    // Return value
    let mut result = ExtractionResult {
        ..Default::default()
    };

    // All pcap-ng files start with a section header; parse it
    if let Ok(section_header) = parse_pcapng_section_block(&file_data[offset..]) {
        let mut block_count: usize = 1;
        let available_data = file_data.len() - offset;
        let mut next_offset = offset + section_header.block_size;
        let mut previous_offset = None;

        // Loop through all blocks in the pcap-ng file
        while is_offset_safe(available_data, next_offset, previous_offset) {
            match file_data.get(next_offset..) {
                None => {
                    break;
                }
                Some(block_data) => {
                    // Parse the next block header
                    match parse_pcapng_block(block_data, &section_header.endianness) {
                        Err(_) => {
                            break;
                        }
                        Ok(block_header) => {
                            // This block looks valid, go to the next one
                            block_count += 1;
                            previous_offset = Some(next_offset);
                            next_offset += block_header.block_size;
                        }
                    }
                }
            }
        }

        // Must have processed the minimum number of blocks
        if block_count >= MIN_BLOCK_COUNT {
            // Everything looks OK
            result.size = Some(next_offset - offset);
            result.success = true;

            // Do extraction if requested
            if output_directory.is_some() {
                let chroot = Chroot::new(output_directory);
                result.success =
                    chroot.carve_file(OUTPUT_FILE_NAME, file_data, offset, result.size.unwrap());
            }
        }
    }

    result
}
