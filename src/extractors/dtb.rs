use crate::common::is_offset_safe;
use crate::extractors::common::{Chroot, ExtractionResult, Extractor, ExtractorType};
use crate::structures::dtb::{parse_dtb_header, parse_dtb_node};
use log::error;

/// Defines the internal extractor function for extracting Device Tree Blobs
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::dtb::dtb_extractor;
///
/// match dtb_extractor().utility {
///     ExtractorType::None => panic!("Invalid extractor type of None"),
///     ExtractorType::Internal(func) => println!("Internal extractor OK: {:?}", func),
///     ExtractorType::External(cmd) => {
///         if let Err(e) = Command::new(&cmd).output() {
///             if e.kind() == ErrorKind::NotFound {
///                 panic!("External extractor '{}' not found", cmd);
///             } else {
///                 panic!("Failed to execute external extractor '{}': {}", cmd, e);
///             }
///         }
///     }
/// }
/// ```
pub fn dtb_extractor() -> Extractor {
    Extractor {
        utility: ExtractorType::Internal(extract_dtb),
        ..Default::default()
    }
}

/// Internal extractor for extracting Device Tree Blobs
pub fn extract_dtb(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&str>,
) -> ExtractionResult {
    let mut heirerarchy: Vec<String> = Vec::new();

    let mut result = ExtractionResult {
        ..Default::default()
    };

    // Parse the DTB file header
    if let Ok(dtb_header) = parse_dtb_header(&file_data[offset..]) {
        // Get all the DTB data
        if let Some(dtb_data) = file_data.get(offset..offset + dtb_header.total_size) {
            // DTB node entries start at the structure offset specified in the DTB header
            let mut entry_offset = dtb_header.struct_offset;
            let mut previous_entry_offset = None;
            let available_data = dtb_data.len();

            // Loop over all DTB node entries
            while is_offset_safe(available_data, entry_offset, previous_entry_offset) {
                // Parse the next DTB node entry
                let node = parse_dtb_node(&dtb_header, dtb_data, entry_offset);

                // Beginning of a node, add it to the heirerarchy list
                if node.begin {
                    if !node.name.is_empty() {
                        heirerarchy.push(node.name.clone());
                    }
                // End of a node, remove it from the heirerarchy list
                } else if node.end {
                    if !heirerarchy.is_empty() {
                        heirerarchy.pop();
                    }
                // End of the DTB structure, return success only if the whole DTB structure was parsed successfully up to the EOF marker
                } else if node.eof {
                    result.success = true;
                    result.size = Some(available_data);
                    break;
                // DTB property, extract it to disk
                } else if node.property {
                    if output_directory.is_some() {
                        let chroot = Chroot::new(output_directory);
                        let dir_path = heirerarchy.join(std::path::MAIN_SEPARATOR_STR);
                        let file_path = chroot.safe_path_join(&dir_path, &node.name);

                        if !chroot.create_directory(dir_path) {
                            break;
                        }

                        if !chroot.create_file(file_path, &node.data) {
                            break;
                        }
                    }
                // The only other supported node type is NOP
                } else if !node.nop {
                    error!("Unknown or invalid DTB node");
                    break;
                }

                // Update offsets to parse the next DTB structure entry
                previous_entry_offset = Some(entry_offset);
                entry_offset += node.total_size;
            }
        }
    }

    result
}
