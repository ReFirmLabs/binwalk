use crate::extractors::common::{Chroot, ExtractionResult, Extractor, ExtractorType};

/// Defines the internal extractor function for carving out JPEG images
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::jpeg::jpeg_extractor;
///
/// match jpeg_extractor().utility {
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
pub fn jpeg_extractor() -> Extractor {
    Extractor {
        do_not_recurse: true,
        utility: ExtractorType::Internal(extract_jpeg_image),
        ..Default::default()
    }
}

/// Internal extractor for carving JPEG images to disk
pub fn extract_jpeg_image(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&str>,
) -> ExtractionResult {
    const OUTFILE_NAME: &str = "image.jpg";

    let mut result = ExtractionResult {
        ..Default::default()
    };

    // Find the JPEG EOF to identify the total JPEG size
    if let Some(jpeg_data_size) = get_jpeg_data_size(&file_data[offset..]) {
        result.size = Some(jpeg_data_size);
        result.success = true;

        if output_directory.is_some() {
            let chroot = Chroot::new(output_directory);
            result.success =
                chroot.carve_file(OUTFILE_NAME, file_data, offset, result.size.unwrap());
        }
    }

    result
}

/// Parses JPEG markers until the EOF marker is found
fn get_jpeg_data_size(jpeg_data: &[u8]) -> Option<usize> {
    const SIZE_FIELD_LENGTH: usize = 2;
    const SOS_SCAN_AHEAD_LENGTH: usize = 2;
    const MARKER_MAGIC: u8 = 0xFF;
    const SOS_MARKER: u8 = 0xDA;
    const EOF_MARKER: u8 = 0xD9;

    let mut next_marker_offset: usize = 0;

    // Most JPEG markers include a size field; these do not
    let no_length_markers: Vec<u8> = vec![
        0x00, 0x01, 0xD0, 0xD1, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, EOF_MARKER,
    ];

    // In a Start Of Scan block, ignore 0xFF marker magics that are followed by one of these bytes
    let sos_skip_markers: Vec<u8> = vec![0x00, 0xD0, 0xD1, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7];

    loop {
        // Read the marker magic byte
        match jpeg_data.get(next_marker_offset) {
            None => {
                break;
            }
            Some(marker_magic) => {
                // Make sure this is the correct marker magic
                if *marker_magic != MARKER_MAGIC {
                    break;
                }

                // Include marker magic byte in side of the marker
                next_marker_offset += 1;

                // Read the marker ID byte
                match jpeg_data.get(next_marker_offset) {
                    None => {
                        break;
                    }
                    Some(marker_id) => {
                        // Include marker ID byte in the size of the marker
                        next_marker_offset += 1;

                        // Most markers have a 2-byte length field after the marker, stored in big-endian
                        if !no_length_markers.contains(marker_id) {
                            match jpeg_data
                                .get(next_marker_offset..next_marker_offset + SIZE_FIELD_LENGTH)
                            {
                                None => {
                                    break;
                                }
                                Some(size_bytes) => {
                                    next_marker_offset +=
                                        u16::from_be_bytes(size_bytes.try_into().unwrap()) as usize;
                                }
                            }
                        }

                        // Start Of Scan markers have a size field, but are immediately followed by data not included int
                        // the size field. Need to scan all the bytes until the next valid JPEG marker is found.
                        if *marker_id == SOS_MARKER {
                            loop {
                                // Get the next two bytes
                                match jpeg_data.get(
                                    next_marker_offset..next_marker_offset + SOS_SCAN_AHEAD_LENGTH,
                                ) {
                                    None => {
                                        break;
                                    }
                                    Some(next_bytes) => {
                                        // Check if the next byte is a marker magic byte, *and* that it is not followed by a marker escape byte
                                        if next_bytes[0] == MARKER_MAGIC
                                            && !sos_skip_markers.contains(&next_bytes[1])
                                        {
                                            break;
                                        } else {
                                            // Go to the next byte
                                            next_marker_offset += 1;
                                        }
                                    }
                                }
                            }
                        }

                        // EOF marker indicates the end of the JPEG image
                        if *marker_id == EOF_MARKER {
                            return Some(next_marker_offset);
                        }
                    }
                }
            }
        }
    }

    None
}
