use crate::common::crc32;
use crate::extractors::common::{Chroot, ExtractionResult, Extractor, ExtractorType};
use crate::structures::uimage::parse_uimage_header;

pub fn uimage_extractor() -> Extractor {
    Extractor {
        utility: ExtractorType::Internal(extract_uimage),
        ..Default::default()
    }
}

pub fn extract_uimage(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&String>,
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

            // Get the raw image data after the uImage header and validate the data CRC
            if let Some(image_data) = file_data.get(image_data_start..image_data_end) {
                if crc32(image_data) == (uimage_header.data_checksum as u32) {
                    result.success = true;
                    result.size = Some(uimage_header.header_size + uimage_header.data_size);

                    // If extraction was requested, carve the uImage data out to a file
                    if output_directory.is_some() {
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
    }

    result
}
