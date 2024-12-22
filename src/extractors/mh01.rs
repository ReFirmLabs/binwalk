use crate::extractors::common::{Chroot, ExtractionResult, Extractor, ExtractorType};
use crate::structures::mh01::parse_mh01_header;

/// Defines the internal extractor function for carving out MH01 firmware images
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::mh01::mh01_extractor;
///
/// match mh01_extractor().utility {
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
pub fn mh01_extractor() -> Extractor {
    Extractor {
        utility: ExtractorType::Internal(extract_mh01_image),
        ..Default::default()
    }
}

/// Internal extractor for carve pieces of MH01 images to disk
pub fn extract_mh01_image(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&str>,
) -> ExtractionResult {
    // File names for the three portions of the MH01 firmware image
    const IV_FILE_NAME: &str = "iv.bin";
    const SIGNATURE_FILE_NAME: &str = "signature.bin";
    const ENCRYPTED_DATA_FILE_NAME: &str = "encrypted.bin";
    const DECRYPTED_DATA_FILE_NAME: &str = "decrypted.bin";

    let mut result = ExtractionResult {
        ..Default::default()
    };

    // Get the MH01 image data
    if let Some(mh01_data) = file_data.get(offset..) {
        // Parse the MH01 header
        if let Ok(mh01_header) = parse_mh01_header(mh01_data) {
            result.size = Some(mh01_header.total_size);

            // If extraction was requested, do it
            if output_directory.is_some() {
                let chroot = Chroot::new(output_directory);

                // Try to decrypt the firmware
                match delink::mh01::decrypt(mh01_data) {
                    Ok(decrypted_data) => {
                        // Write decrypted data to disk
                        result.success =
                            chroot.create_file(DECRYPTED_DATA_FILE_NAME, &decrypted_data);
                    }
                    Err(_) => {
                        // Decryption failture; extract each part of the firmware image, ensuring that each one extracts without error
                        result.success = chroot.carve_file(
                            IV_FILE_NAME,
                            mh01_data,
                            mh01_header.iv_offset,
                            mh01_header.iv_size,
                        ) && chroot.carve_file(
                            SIGNATURE_FILE_NAME,
                            mh01_data,
                            mh01_header.signature_offset,
                            mh01_header.signature_size,
                        ) && chroot.carve_file(
                            ENCRYPTED_DATA_FILE_NAME,
                            mh01_data,
                            mh01_header.encrypted_data_offset,
                            mh01_header.encrypted_data_size,
                        );
                    }
                }
            // No extraction requested, just return success
            } else {
                result.success = true;
            }
        }
    }

    result
}
