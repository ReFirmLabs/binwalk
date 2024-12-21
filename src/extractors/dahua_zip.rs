use crate::extractors::common::{Chroot, ExtractionResult, Extractor, ExtractorType};
use crate::signatures::zip::find_zip_eof;

/// Defines the internal extractor function for carving Dahua ZIP files
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::dahua_zip::dahua_zip_extractor;
///
/// match dahua_zip_extractor().utility {
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
pub fn dahua_zip_extractor() -> Extractor {
    Extractor {
        utility: ExtractorType::Internal(extract_dahua_zip),
        ..Default::default()
    }
}

/// Carves out a Dahua ZIP file and converts it to a normal ZIP file
pub fn extract_dahua_zip(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&str>,
) -> ExtractionResult {
    const OUTFILE_NAME: &str = "dahua.zip";
    const ZIP_HEADER: &[u8] = b"PK";

    let mut result = ExtractionResult {
        ..Default::default()
    };

    // Locate the end of the zip archive
    if let Ok(zip_info) = find_zip_eof(file_data, offset) {
        // Calculate total size of the zip archive, report success
        result.size = Some(zip_info.eof - offset);
        result.success = true;

        // If extraction was requested, carve the zip archive to disk, replacing the Dahua ZIP magic bytes
        // with the standard ZIP magic bytes.
        if output_directory.is_some() {
            // Start and end offsets of the data to carve
            let start_data = offset + ZIP_HEADER.len();
            let end_data = offset + result.size.unwrap();

            let chroot = Chroot::new(output_directory);

            // Get the data to carve
            match file_data.get(start_data..end_data) {
                None => {
                    result.success = false;
                }
                Some(zip_data) => {
                    // First write the normal ZIP header magic bytes to disk
                    if !chroot.create_file(OUTFILE_NAME, ZIP_HEADER) {
                        result.success = false;
                    } else {
                        // Append the rest of the ZIP archive to disk
                        result.success = chroot.append_to_file(OUTFILE_NAME, zip_data);
                    }
                }
            }
        }
    }

    result
}
