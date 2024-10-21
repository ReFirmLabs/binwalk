use crate::extractors::common::{Chroot, ExtractionResult, Extractor, ExtractorType};
use aho_corasick::AhoCorasick;

/// Defines the internal extractor function for carving out PEM keys
pub fn pem_key_extractor() -> Extractor {
    Extractor {
        do_not_recurse: true,
        utility: ExtractorType::Internal(pem_key_carver),
        ..Default::default()
    }
}

/// Internal extractor function for carving out PEM certs
pub fn pem_certificate_extractor() -> Extractor {
    Extractor {
        do_not_recurse: true,
        utility: ExtractorType::Internal(pem_certificate_carver),
        ..Default::default()
    }
}

pub fn pem_certificate_carver(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&String>,
) -> ExtractionResult {
    const CERTIFICATE_FILE_NAME: &str = "pem.crt";
    pem_carver(
        file_data,
        offset,
        output_directory,
        Some(CERTIFICATE_FILE_NAME),
    )
}

pub fn pem_key_carver(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&String>,
) -> ExtractionResult {
    const KEY_FILE_NAME: &str = "pem.key";
    pem_carver(file_data, offset, output_directory, Some(KEY_FILE_NAME))
}

pub fn pem_carver(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&String>,
    fname: Option<&str>,
) -> ExtractionResult {
    let mut result = ExtractionResult {
        ..Default::default()
    };

    if let Some(pem_size) = get_pem_size(file_data, offset) {
        result.size = Some(pem_size);
        result.success = true;

        if let Some(outfile) = fname {
            if output_directory.is_some() {
                let chroot = Chroot::new(output_directory);
                result.success =
                    chroot.carve_file(outfile, file_data, offset, result.size.unwrap());
            }
        }
    }

    result
}

fn get_pem_size(file_data: &[u8], start_of_pem_offset: usize) -> Option<usize> {
    let eof_markers = vec![
        b"-----END PUBLIC KEY-----".to_vec(),
        b"-----END CERTIFICATE-----".to_vec(),
        b"-----END PRIVATE KEY-----".to_vec(),
        b"-----END EC PRIVATE KEY-----".to_vec(),
        b"-----END RSA PRIVATE KEY-----".to_vec(),
        b"-----END DSA PRIVATE KEY-----".to_vec(),
        b"-----END OPENSSH PRIVATE KEY-----".to_vec(),
    ];

    let newline_chars: Vec<u8> = vec![0x0D, 0x0A];

    let grep = AhoCorasick::new(eof_markers.clone()).unwrap();

    // Find the first end marker
    if let Some(eof_match) = grep
        .find_overlapping_iter(&file_data[start_of_pem_offset..])
        .next()
    {
        let eof_marker_index: usize = eof_match.pattern().as_usize();
        let mut pem_size = eof_match.start() + eof_markers[eof_marker_index].len();

        // Include any trailing newline characters in the total size of the PEM file
        while (start_of_pem_offset + pem_size) < file_data.len() {
            if newline_chars.contains(&file_data[start_of_pem_offset + pem_size]) {
                pem_size += 1;
            } else {
                break;
            }
        }

        return Some(pem_size);
    }

    None
}
