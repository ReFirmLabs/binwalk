use crate::extractors::common::{Chroot, ExtractionResult, Extractor, ExtractorType};
use crate::structures::bmp::{get_dib_header_size, parse_bmp_file_header};

/// Defines the internal extractor function for carving out GIF images
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::bmp::bmp_extractor;
///
/// match bmp_extractor().utility {
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
pub fn bmp_extractor() -> Extractor {
    Extractor {
        do_not_recurse: true,
        utility: ExtractorType::Internal(extract_bmp_image),
        ..Default::default()
    }
}

pub fn extract_bmp_image(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&str>,
) -> ExtractionResult {
    const OUTFILE_NAME: &str = "image.bmp";

    let mut result = ExtractionResult {
        ..Default::default()
    };
    result.success = false;

    // Parse the bmp_file_header
    if let Ok(bmp_file_header) = parse_bmp_file_header(&file_data[offset..]) {
        // https://learn.microsoft.com/en-us/windows/win32/api/wingdi/ns-wingdi-bitmapfileheader
        // The size of the BMP file header
        const BMP_FILE_HEADER_SIZE: usize = 14;

        // Retrieve the size of the header following the BMP file header
        if let Ok(bmp_header_size) =
            get_dib_header_size(&file_data[(offset + BMP_FILE_HEADER_SIZE)..])
        {
            // The offset that points to the image data cannot point into the second header
            if bmp_file_header.bitmap_bits_offset >= (BMP_FILE_HEADER_SIZE + bmp_header_size) {
                // If it was parsed successfully, get the file size
                result.size = Some(bmp_file_header.size);
                result.success = true;

                if output_directory.is_some() {
                    let chroot = Chroot::new(output_directory);
                    result.success =
                        chroot.carve_file(OUTFILE_NAME, file_data, offset, bmp_file_header.size);
                }
            }
        }
    }

    result
}
