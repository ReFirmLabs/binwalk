use crate::extractors::pem;
use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_HIGH};
use base64::prelude::BASE64_STANDARD;
use base64::Engine;

pub const PEM_PUBLIC_KEY_DESCRIPTION: &str = "PEM public key";
pub const PEM_PRIVATE_KEY_DESCRIPTION: &str = "PEM private key";
pub const PEM_CERTIFICATE_DESCRIPTION: &str = "PEM certificate";

pub fn pem_public_key_magic() -> Vec<Vec<u8>> {
    return vec![b"-----BEGIN PUBLIC KEY-----".to_vec()];
}

pub fn pem_private_key_magic() -> Vec<Vec<u8>> {
    return vec![
        b"-----BEGIN PRIVATE KEY-----".to_vec(),
        b"-----BEGIN EC PRIVATE KEY-----".to_vec(),
        b"-----BEGIN RSA PRIVATE KEY-----".to_vec(),
        b"-----BEGIN DSA PRIVATE KEY-----".to_vec(),
        b"-----BEGIN OPENSSH PRIVATE KEY-----".to_vec(),
    ];
}

pub fn pem_certificate_magic() -> Vec<Vec<u8>> {
    return vec![b"-----BEGIN CERTIFICATE-----".to_vec()];
}

// Validates both PEM certificates and keys
pub fn pem_parser(file_data: &Vec<u8>, offset: usize) -> Result<SignatureResult, SignatureError> {
    const MIN_PEM_LEN: usize = 26;

    let mut result = SignatureResult {
        offset: offset,
        confidence: CONFIDENCE_HIGH,
        ..Default::default()
    };

    /*
     * Build a list of magic signatures for public, prvate, and certificate PEMs.
     * These magics are truncated to MIN_PEM_LEN bytes, which is enough to check if
     * the matching signature was a public key, private key, or certificate, which is
     * all we need to know for displaying a useful description string.
     */
    let mut public_magics: Vec<Vec<u8>> = vec![];
    let mut private_magics: Vec<Vec<u8>> = vec![];
    let mut certificate_magics: Vec<Vec<u8>> = vec![];

    for public_magic in pem_public_key_magic() {
        public_magics.push(public_magic[0..MIN_PEM_LEN].to_vec());
    }

    for private_magic in pem_private_key_magic() {
        private_magics.push(private_magic[0..MIN_PEM_LEN].to_vec());
    }

    for cert_magic in pem_certificate_magic() {
        certificate_magics.push(cert_magic[0..MIN_PEM_LEN].to_vec());
    }

    // Sanity check available data
    if file_data.len() > (offset + MIN_PEM_LEN) {
        // Grab the magic bytes for this PEM candidate
        let pem_magic = &file_data[offset..offset + MIN_PEM_LEN].to_vec();

        // Check if this magic is for a PEM cert or a PEM key
        if public_magics.contains(pem_magic) == true {
            result.description = PEM_PUBLIC_KEY_DESCRIPTION.to_string();
        } else if private_magics.contains(pem_magic) == true {
            result.description = PEM_PRIVATE_KEY_DESCRIPTION.to_string();
        } else if certificate_magics.contains(pem_magic) == true {
            result.description = PEM_CERTIFICATE_DESCRIPTION.to_string();
        } else {
            // This function will only be called if one of the magics was found, so this should never happen
            return Err(SignatureError);
        }

        // Do an extraction dry-run to validate that this PEM file looks sane
        let dry_run = pem::pem_carver(file_data, offset, None, None);
        if dry_run.success == true {
            if let Some(pem_size) = dry_run.size {
                // Make sure the PEM data can be base64 decoded
                if let Ok(_) = decode_pem_data(&file_data[offset..offset + pem_size]) {
                    // If the file starts and end with this PEM data, no sense in carving it out to another file on disk
                    if offset == 0 && pem_size == file_data.len() {
                        result.extraction_declined = true;
                    }

                    result.size = pem_size;
                    return Ok(result);
                }
            }
        }
    }

    return Err(SignatureError);
}

fn decode_pem_data(pem_file_data: &[u8]) -> Result<usize, SignatureError> {
    const DELIM: &str = "--";

    // Make sure the PEM data can be converted to a string
    if let Ok(pem_file_string) = String::from_utf8(pem_file_data.to_vec()) {
        let mut delim_count: usize = 0;
        let mut base64_string: String = "".to_string();

        // Loop through PEM file lines
        for line in pem_file_string.lines() {
            // PEM begin and end delimiter strings both start with hyphens
            if line.starts_with(DELIM) {
                delim_count += 1;
                continue;
            }

            // Expect two delimiters: the start, and the end. If we've found both, break.
            if delim_count == 2 {
                break;
            }

            // This is not a delimiter string, append the line to the base64 string to be decoded
            base64_string.push_str(line);
        }

        // If we found some text between the delimiters, attempt to base64 decode it
        if base64_string.len() > 0 {
            // PEM contents are base64 encoded, they should decode OK; if not, it's a false positive
            if let Ok(decoded_data) = BASE64_STANDARD.decode(&base64_string) {
                return Ok(decoded_data.len());
            }
        }
    }

    return Err(SignatureError);
}
