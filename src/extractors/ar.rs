use std::io::{Cursor, Read};

use crate::extractors::{
    self,
    common::{Chroot, ExtractionResult},
};

/// Describes how to run the ar utility to extract GNU/BSD/DEB archives
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::deb::deb_extractor;
///
/// match ar_extractor().utility {
///     ExtractorType::Internal(func) => func(file_data, offset, Some(output_directory)),
///     _ => unreachable!("Invalid extractor type"),
///  }
/// ```
pub fn ar_extractor() -> extractors::common::Extractor {
    extractors::common::Extractor {
        utility: extractors::common::ExtractorType::Internal(extract_ar_file),
        extension: "deb".to_string(),
        do_not_recurse: false,
        ..Default::default()
    }
}

pub fn extract_ar_file(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&str>,
) -> ExtractionResult {
    let mut result = ExtractionResult {
        success: true,
        size: Some(0),
        do_not_recurse: false,
        ..Default::default()
    };

    let mut reader = Cursor::new(file_data);
    reader.set_position(offset as u64);
    let mut archive = ar::Archive::new(reader);
    while let Some(entry_result) = archive.next_entry() {
        if let Ok(mut entry) = entry_result {
            if !output_directory.is_none() {
                let chroot = Chroot::new(output_directory);

                // it would be nicer if Chroot::create_file were to take a impl Cursor<u8> instead
                // of a Vec<u8>, then we would use less memory:
                let mut data = vec![];
                if let Ok(size) = entry.read_to_end(&mut data) {
                    result.size.as_mut().map(|x| *x += size);
                    result.success &= chroot
                        .create_file(String::from_utf8_lossy(entry.header().identifier()), &data);
                }
            }
        }
    }

    result
}
