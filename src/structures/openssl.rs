use crate::structures::common::{self, StructureError};

/// Struct to store info on an OpenSSL crypto header
pub struct OpenSSLCryptHeader {
    pub salt: usize,
}

/// Parse an OpenSSl crypto header
pub fn parse_openssl_crypt_header(ssl_data: &[u8]) -> Result<OpenSSLCryptHeader, StructureError> {
    let ssl_structure = vec![("magic", "u32"), ("salt", "u64")];

    if let Ok(ssl_header) = common::parse(ssl_data, &ssl_structure, "big") {
        return Ok(OpenSSLCryptHeader {
            salt: ssl_header["salt"],
        });
    }

    Err(StructureError)
}
