use crate::common::crc32;
use crate::extractors::common::{Chroot, ExtractionResult, Extractor, ExtractorType};
use crate::structures::uimage::parse_uimage_header;

/// Describes the internal extractor for carving uImage files to disk
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::uimage::uimage_extractor;
///
/// match uimage_extractor().utility {
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
pub fn uimage_extractor() -> Extractor {
    Extractor {
        utility: ExtractorType::Internal(extract_uimage),
        ..Default::default()
    }
}

pub fn extract_uimage(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&str>,
) -> ExtractionResult {
    // If no name is povided in the uImage header, use this as the output file name
    const DEFAULT_OUTPUT_FILE_NAME: &str = "uimage_data";
    const OUTPUT_FILE_EXT: &str = "bin";

    let mut result = ExtractionResult {
        ..Default::default()
    };

    // Get the uImage data and parse the header
    if let Some(uimage_header_data) = file_data.get(offset..) {
        if let Ok(uimage_header) = parse_uimage_header(uimage_header_data) {
            let image_data_start = offset + uimage_header.header_size;
            let image_data_end = image_data_start + uimage_header.data_size;

            // Get the raw image data after the uImage header to validate the data CRC
            if let Some(image_data) = file_data.get(image_data_start..image_data_end) {
                result.success = true;
                result.size = Some(uimage_header.header_size);

                // Check the data CRC
                let data_crc_valid: bool =
                    crc32(image_data) == (uimage_header.data_checksum as u32);

                // If the data CRC is valid, include the size of the data in the reported size
                if data_crc_valid {
                    result.size = Some(result.size.unwrap() + uimage_header.data_size);
                }

                // If extraction was requested and the data CRC is valid, carve the uImage data out to a file
                if data_crc_valid && output_directory.is_some() {
                    let chroot = Chroot::new(output_directory);
                    let mut file_base_name: String = DEFAULT_OUTPUT_FILE_NAME.to_string();

                    // Use the name specified in the uImage header as the file name, if one was provided
                    if !uimage_header.name.is_empty() {
                        file_base_name = uimage_header.name.replace(" ", "_");
                    }

                    let output_file = format!("{}.{}", file_base_name, OUTPUT_FILE_EXT);

                    result.success = chroot.create_file(&output_file, image_data);
                }
            }
        }
    }

    result
}
