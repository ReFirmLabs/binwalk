use crate::common::is_offset_safe;
use crate::extractors::common::{Chroot, ExtractionResult, Extractor, ExtractorType};
use crate::structures::common::StructureError;
use crate::structures::gif::{parse_gif_extension, parse_gif_header, parse_gif_image_descriptor};

/// Defines the internal extractor function for carving out JPEG images
pub fn gif_extractor() -> Extractor {
    Extractor {
        do_not_recurse: true,
        utility: ExtractorType::Internal(extract_gif_image),
        ..Default::default()
    }
}

/// Parses and carves a GIF image from a file
pub fn extract_gif_image(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&String>,
) -> ExtractionResult {
    const OUTFILE_NAME: &str = "image.gif";

    let mut result = ExtractionResult {
        ..Default::default()
    };

    // Parse the GIF header
    if let Ok(gif_header) = parse_gif_header(&file_data[offset..]) {
        // GIF data follows the gif header
        if let Some(gif_image_data) = file_data.get(offset + gif_header.size..) {
            // Determine the size of the GIF image data
            if let Some(gif_data_size) = get_gif_data_size(gif_image_data) {
                // Report success
                result.size = Some(gif_header.size + gif_data_size);
                result.success = true;

                // Do extraction, if requested
                if output_directory.is_some() {
                    let chroot = Chroot::new(output_directory);
                    result.success =
                        chroot.carve_file(OUTFILE_NAME, file_data, offset, result.size.unwrap());
                }
            }
        }
    }

    result
}

/// Returns the size of the GIF data that follows the GIF header
fn get_gif_data_size(gif_data: &[u8]) -> Option<usize> {
    // GIF block types
    const EXTENSION: u8 = 0x21;
    const TERMINATOR: u8 = 0x3B;
    const IMAGE_DESCRIPTOR: u8 = 0x2C;

    let mut next_offset: usize = 0;
    let mut previous_offset = None;
    let available_data = gif_data.len();

    // Loop through all GIF data blocks
    while is_offset_safe(available_data, next_offset, previous_offset) {
        let block_size: Result<usize, StructureError>;

        // Get the block type of the next block
        match gif_data.get(next_offset) {
            None => break,
            Some(block_type) => {
                // Parse the block type accordingly
                if *block_type == IMAGE_DESCRIPTOR {
                    block_size = parse_gif_image_descriptor(&gif_data[next_offset..]);
                } else if *block_type == EXTENSION {
                    block_size = parse_gif_extension(&gif_data[next_offset..]);
                } else if *block_type == TERMINATOR {
                    // Only return the GIF size if we've found a termination block.
                    // The +1 is for the size of the block_type u8.
                    return Some(next_offset + 1);
                } else {
                    break;
                }
            }
        }

        // Check if the block was parsed successfully
        match block_size {
            Err(_) => break,
            Ok(this_block_size) => {
                // Everything looks OK, go to the next block
                previous_offset = Some(next_offset);
                next_offset += this_block_size;
            }
        }
    }

    // Something went wrong, failure
    None
}
