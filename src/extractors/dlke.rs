use crate::extractors::common::{Chroot, ExtractionResult, Extractor, ExtractorType};
use crate::structures::jboot::parse_jboot_arm_header;

/// Defines the internal extractor function for carving out D-Link TLV firmware images
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::dlke::dlke_extractor;
///
/// match dlke_extractor().utility {
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
pub fn dlke_extractor() -> Extractor {
    Extractor {
        utility: ExtractorType::Internal(extract_dlke_image),
        ..Default::default()
    }
}

/// Internal extractor for carve pieces of encrypted DLKE firmware images to disk
pub fn extract_dlke_image(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&String>,
) -> ExtractionResult {
    const ENCRYPTED_FILE_NAME: &str = "encrypted.bin";
    const SIGNATURE_FILE_NAME: &str = "signature.bin";

    let mut result = ExtractionResult {
        ..Default::default()
    };

    // Parse the first header, which describes the size of the firmware signature
    if let Some(dlke_sig_header_data) = file_data.get(offset..) {
        if let Ok(dlke_signature_header) = parse_jboot_arm_header(dlke_sig_header_data) {
            // Second header should immediately follow the first
            if let Some(dlke_crypt_header_data) = file_data
                .get(offset + dlke_signature_header.header_size + dlke_signature_header.data_size..)
            {
                // Parse the second header, which describes the size of the encrypted data
                if let Ok(dlke_crypt_header) = parse_jboot_arm_header(dlke_crypt_header_data) {
                    result.success = true;
                    result.size = Some(
                        dlke_signature_header.header_size
                            + dlke_signature_header.data_size
                            + dlke_crypt_header.header_size
                            + dlke_crypt_header.data_size,
                    );

                    if output_directory.is_some() {
                        let chroot = Chroot::new(output_directory);

                        if !chroot.carve_file(
                            SIGNATURE_FILE_NAME,
                            dlke_sig_header_data,
                            dlke_signature_header.header_size,
                            dlke_signature_header.data_size,
                        ) || !chroot.carve_file(
                            ENCRYPTED_FILE_NAME,
                            dlke_crypt_header_data,
                            dlke_crypt_header.header_size,
                            dlke_crypt_header.data_size,
                        ) {
                            result.success = false;
                        }
                    }
                }
            }
        }
    }

    result
}
