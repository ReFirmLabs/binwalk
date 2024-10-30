use crate::common::is_offset_safe;
use crate::extractors::common::{Chroot, ExtractionResult, Extractor, ExtractorType};
use crate::structures::wince::{parse_wince_block_header, parse_wince_header};

/// Defines the internal extractor function for extracting Windows CE images
pub fn wince_extractor() -> Extractor {
    Extractor {
        utility: ExtractorType::Internal(wince_dump),
        ..Default::default()
    }
}

/// Internal extractor for extracting data blocks from Windows CE images
pub fn wince_dump(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&String>,
) -> ExtractionResult {
    let mut result = ExtractionResult {
        ..Default::default()
    };

    // Parse the file header
    if let Some(wince_data) = file_data.get(offset..) {
        if let Ok(wince_header) = parse_wince_header(wince_data) {
            // Get the block data, immediately following the file header
            if let Some(wince_block_data) = wince_data.get(wince_header.header_size..) {
                // Process all blocks in the block data
                if let Some(data_blocks) = process_wince_blocks(wince_block_data) {
                    // The first block entry's address should equal the WinCE header's base address
                    if data_blocks.entries[0].address == wince_header.base_address {
                        // Block processing was successful
                        result.success = true;
                        result.size = Some(wince_header.header_size + data_blocks.total_size);

                        // If extraction was requested, extract each block to a file on disk
                        if output_directory.is_some() {
                            let chroot = Chroot::new(output_directory);

                            for block in data_blocks.entries {
                                let block_file_name = format!("{:X}.bin", block.address);

                                // If file carving fails, report a failure to extract
                                if !chroot.carve_file(
                                    block_file_name,
                                    wince_block_data,
                                    block.offset,
                                    block.size,
                                ) {
                                    result.success = false;
                                    break;
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    result
}

/// Stores info about each WinCE block
#[derive(Debug, Default, Clone)]
struct BlockInfo {
    pub address: usize,
    pub offset: usize,
    pub size: usize,
}

/// Stores info about all WinCE blocks
#[derive(Debug, Default, Clone)]
struct BlockData {
    pub total_size: usize,
    pub entries: Vec<BlockInfo>,
}

/// Process all WinCE blocks
fn process_wince_blocks(blocks_data: &[u8]) -> Option<BlockData> {
    // Arbitrarily chosen, just to make sure more than one or two blocks were processed and sane
    const MIN_ENTRIES_COUNT: usize = 5;

    let mut blocks = BlockData {
        ..Default::default()
    };

    let mut next_offset: usize = 0;
    let mut previous_offset = None;
    let available_data = blocks_data.len();

    // Process all blocks until the end block is reached, or an error is encountered
    while is_offset_safe(available_data, next_offset, previous_offset) {
        // Parse this block's header
        match parse_wince_block_header(&blocks_data[next_offset..]) {
            Err(_) => {
                break;
            }
            Ok(block_header) => {
                // Include the block header size in the total size of the block data
                blocks.total_size += block_header.header_size;

                // A block header address of NULL indicates EOF
                if block_header.address == 0 {
                    // Sanity check the number of blocks processed
                    if blocks.entries.len() > MIN_ENTRIES_COUNT {
                        return Some(blocks);
                    } else {
                        break;
                    }
                } else {
                    // Include this block's size in the total size of the block data
                    blocks.total_size += block_header.data_size;

                    // Add this block to the list of block entries
                    blocks.entries.push(BlockInfo {
                        address: block_header.address,
                        offset: next_offset + block_header.header_size,
                        size: block_header.data_size,
                    });

                    // Update the offsets for the next loop iteration
                    previous_offset = Some(next_offset);
                    next_offset += block_header.header_size + block_header.data_size;
                }
            }
        }
    }

    None
}
