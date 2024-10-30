use crate::common::is_offset_safe;
use crate::extractors::common::{Chroot, ExtractionResult, Extractor, ExtractorType};
use crate::structures::wince::{parse_wince_block_header, parse_wince_header};

/// Defines the internal extractor function for extracting Windows CE images
pub fn wince_extractor() -> Extractor {
    return Extractor {
        utility: ExtractorType::Internal(wince_dump),
        ..Default::default()
    };
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

    if let Some(wince_data) = file_data.get(offset..) {
        if let Ok(wince_header) = parse_wince_header(&file_data) {
            if let Some(wince_block_data) = wince_data.get(wince_header.header_size..) {
                if let Some(data_blocks) = process_wince_blocks(wince_block_data) {
                    result.success = true;
                    result.size = Some(wince_header.header_size + data_blocks.total_size);

                    if output_directory.is_some() {
                        let chroot = Chroot::new(output_directory);

                        for block in data_blocks.blocks {
                            let block_file_name = format!("{:X}.bin", block.address);

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

    result
}

#[derive(Debug, Default, Clone)]
struct BlockInfo {
    pub address: usize,
    pub offset: usize,
    pub size: usize,
}

#[derive(Debug, Default, Clone)]
struct BlockData {
    pub total_size: usize,
    pub blocks: Vec<BlockInfo>,
}

fn process_wince_blocks(blocks_data: &[u8]) -> Option<BlockData> {
    const MIN_BLOCK_COUNT: usize = 3;

    let mut blocks = BlockData {
        ..Default::default()
    };
    let mut next_offset: usize = 0;
    let mut previous_offset = None;
    let available_data = blocks_data.len();

    while is_offset_safe(available_data, next_offset, previous_offset) {
        match parse_wince_block_header(&blocks_data[next_offset..]) {
            Err(_) => {
                break;
            }
            Ok(block_header) => {
                blocks.total_size += block_header.header_size;

                if block_header.address == 0 {
                    if blocks.blocks.len() > MIN_BLOCK_COUNT {
                        return Some(blocks);
                    } else {
                        break;
                    }
                } else {
                    blocks.total_size += block_header.data_size;
                    blocks.blocks.push(BlockInfo {
                        address: block_header.address,
                        offset: next_offset + block_header.header_size,
                        size: block_header.data_size,
                    });
                    previous_offset = Some(next_offset);
                    next_offset += block_header.header_size + block_header.data_size;
                }
            }
        }
    }

    None
}
