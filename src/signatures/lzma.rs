use crate::extractors::lzma;
use crate::signatures;
use crate::structures::lzma::parse_lzma_header;

pub const DESCRIPTION: &str = "LZMA compressed data";

pub fn lzma_magic() -> Vec<Vec<u8>> {
    let mut magic_signatures: Vec<Vec<u8>> = vec![];

    // Common LZMA properties
    let supported_properties: Vec<u8> = vec![0x5D, 0x6E, 0x6D, 0x6C];

    let supported_dictionary_sizes: Vec<u32> = vec![
        0x10_00_00_00,
        0x20_00_00_00,
        0x01_00_00_00,
        0x02_00_00_00,
        0x04_00_00_00,
        0x00_80_00_00,
        0x00_40_00_00,
        0x00_20_00_00,
        0x00_10_00_00,
        0x00_08_00_00,
        0x00_02_00_00,
        0x00_01_00_00,
    ];

    /*
     * Build a list of magic signatures to search for based on the supported property and dictionary values.
     * This means having a lot of LZMA signatures, but they are less prone to false positives than searching
     * for a more generic, but shorter, signature, such as b"\x5d\x00\x00". This results in less validation
     * of false positives, improving analysis times.
     */
    for property in supported_properties {
        for dictionary_size in &supported_dictionary_sizes {
            let mut magic: Vec<u8> = vec![property];
            magic.extend(dictionary_size.to_le_bytes().to_vec());
            magic_signatures.push(magic.to_vec());
        }
    }

    return magic_signatures;
}

pub fn lzma_parser(
    file_data: &Vec<u8>,
    offset: usize,
) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {
    let mut result = signatures::common::SignatureResult {
        offset: offset,
        description: DESCRIPTION.to_string(),
        confidence: signatures::common::CONFIDENCE_HIGH,
        ..Default::default()
    };

    if let Ok(lzma_header) = parse_lzma_header(&file_data[offset..]) {
        /*
         * LZMA signatures are very prone to false positives, so do a dry-run extraction.
         * If it succeeds, we have high confidence that this signature is valid.
         * Else, assume this is a false positive.
         */
        let dry_run = lzma::lzma_decompress(file_data, offset, None);
        if dry_run.success == true {
            result.description = format!(
                "{}, properties: {:#04X}, dictionary size: {} bytes, uncompressed size: {} bytes",
                result.description,
                lzma_header.properties,
                lzma_header.dictionary_size,
                lzma_header.decompressed_size
            );
            return Ok(result);
        }
    }

    return Err(signatures::common::SignatureError);
}
