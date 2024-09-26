use crate::structures;

pub struct OpenSSLCryptHeader {
    pub salt: usize,
}

pub fn parse_openssl_crypt_header(
    ssl_data: &[u8],
) -> Result<OpenSSLCryptHeader, structures::common::StructureError> {
    let ssl_structure = vec![("magic", "u32"), ("salt", "u64")];

    if let Ok(ssl_header) = structures::common::parse(&ssl_data, &ssl_structure, "big") {

        return Ok(OpenSSLCryptHeader {
            salt: ssl_header["salt"],
        });
    }

    return Err(structures::common::StructureError);
}
