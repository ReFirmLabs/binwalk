use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_MEDIUM};

/// Human readable description
pub const DESCRIPTION: &str = "bzip2 compressed data";

/// Bzip2 magic bytes; includes the magic bytes, version number, block size, and compressed magic signature
pub fn bzip2_magic() -> Vec<Vec<u8>> {
    return vec![
        b"BZh91AY&SY".to_vec(),
        b"BZh81AY&SY".to_vec(),
        b"BZh71AY&SY".to_vec(),
        b"BZh61AY&SY".to_vec(),
        b"BZh51AY&SY".to_vec(),
        b"BZh41AY&SY".to_vec(),
        b"BZh31AY&SY".to_vec(),
        b"BZh21AY&SY".to_vec(),
        b"BZh11AY&SY".to_vec(),
    ];
}

/// Bzip2 header parser
pub fn bzip2_parser(
    _file_data: &Vec<u8>,
    offset: usize,
) -> Result<SignatureResult, SignatureError> {
    // Return value
    let result = SignatureResult {
        description: DESCRIPTION.to_string(),
        offset: offset,
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    /*
     * Signature is long enough that, currently, we just assume it's valid
     * The full bz2 header structure does contain a CRC, but this appears to
     * be the CRC of the uncompressed data, and while there is an end-of-stream
     * marker, it is not guarunteed to be byte-aligned (https://en.wikipedia.org/wiki/Bzip2).
     */
    return Ok(result);
}
