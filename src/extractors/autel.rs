use crate::extractors::common::{Chroot, ExtractionResult, Extractor, ExtractorType};
use crate::structures::autel::parse_autel_header;

const BLOCK_SIZE: usize = 256;

/// Defines the internal extractor function for deobfuscating Autel firmware
pub fn autel_extractor() -> Extractor {
    Extractor {
        utility: ExtractorType::Internal(autel_deobfuscate),
        ..Default::default()
    }
}

/// Internal extractor for obfuscated Autel firmware
/// https://gist.github.com/sector7-nl/3fc815cd2497817ad461bfbd393294cb
pub fn autel_deobfuscate(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&String>,
) -> ExtractionResult {
    const OUTPUT_FILE_NAME: &str = "autel.decoded";

    let mut result = ExtractionResult {
        ..Default::default()
    };

    // Parse and validate the header
    if let Ok(autel_header) = parse_autel_header(&file_data[offset..]) {
        // Get the start and end offsets of the actual encoded data
        let data_start = offset + autel_header.header_size;
        let data_end = data_start + autel_header.data_size;

        // Get the encoded data
        if let Some(autel_data) = file_data.get(data_start..data_end) {
            // Interate through each block of the encoded data
            let mut block_iter = autel_data.chunks(BLOCK_SIZE);

            loop {
                match block_iter.next() {
                    None => {
                        // EOF
                        result.size = Some(autel_header.data_size);
                        result.success = true;
                        break;
                    }
                    Some(block_bytes) => {
                        // Decode the data block
                        let decoded_block = decode_autel_block(block_bytes);

                        // Write to file, if requested
                        if output_directory.is_some() {
                            let chroot = Chroot::new(output_directory);
                            if !chroot.append_to_file(OUTPUT_FILE_NAME, &decoded_block) {
                                break;
                            }
                        }
                    }
                }
            }
        }
    }

    result
}

/// Block decoder for autel encoded firmware.
/// block_data *must* be 256 bytes in size, or less.
fn decode_autel_block(block_data: &[u8]) -> Vec<u8> {
    // Lookup table for encoding/decoding bytes
    let encoding_table: Vec<(usize, usize)> = vec![
        (54, 147),
        (96, 129),
        (59, 193),
        (191, 0),
        (45, 130),
        (96, 144),
        (27, 129),
        (152, 0),
        (44, 180),
        (118, 141),
        (115, 129),
        (210, 0),
        (13, 164),
        (27, 133),
        (20, 192),
        (139, 0),
        (28, 166),
        (17, 133),
        (19, 193),
        (224, 0),
        (20, 161),
        (145, 0),
        (14, 193),
        (12, 132),
        (18, 161),
        (17, 140),
        (29, 192),
        (246, 0),
        (115, 178),
        (28, 132),
        (155, 0),
        (12, 132),
        (31, 165),
        (20, 136),
        (27, 193),
        (142, 0),
        (96, 164),
        (18, 133),
        (145, 0),
        (23, 132),
        (13, 165),
        (13, 148),
        (23, 193),
        (19, 132),
        (27, 178),
        (83, 137),
        (146, 0),
        (145, 0),
        (18, 166),
        (96, 148),
        (13, 193),
        (159, 0),
        (96, 166),
        (20, 129),
        (20, 193),
        (27, 132),
        (9, 160),
        (96, 148),
        (13, 192),
        (159, 0),
        (96, 180),
        (142, 0),
        (31, 193),
        (155, 0),
        (7, 166),
        (224, 0),
        (20, 192),
        (27, 132),
        (28, 160),
        (17, 149),
        (19, 193),
        (96, 132),
        (76, 164),
        (208, 0),
        (80, 192),
        (78, 132),
        (96, 160),
        (27, 144),
        (24, 193),
        (140, 0),
        (96, 178),
        (17, 141),
        (12, 193),
        (224, 0),
        (14, 161),
        (17, 141),
        (151, 0),
        (14, 132),
        (16, 165),
        (96, 137),
        (13, 193),
        (155, 0),
        (20, 161),
        (29, 141),
        (23, 192),
        (24, 132),
        (27, 178),
        (10, 133),
        (96, 192),
        (140, 0),
        (14, 180),
        (17, 133),
        (16, 192),
        (144, 0),
        (11, 163),
        (13, 141),
        (96, 192),
        (17, 132),
        (12, 178),
        (96, 141),
        (28, 192),
        (27, 132),
        (27, 130),
        (18, 141),
        (96, 193),
        (31, 132),
        (96, 181),
        (13, 140),
        (23, 193),
        (224, 0),
        (27, 166),
        (142, 0),
        (27, 192),
        (24, 132),
        (12, 183),
        (96, 133),
        (84, 192),
        (14, 132),
        (27, 178),
        (10, 140),
        (155, 0),
        (9, 132),
        (17, 160),
        (56, 133),
        (96, 192),
        (82, 132),
        (13, 160),
        (27, 137),
        (20, 193),
        (139, 0),
        (28, 161),
        (145, 0),
        (19, 192),
        (118, 132),
        (115, 165),
        (20, 132),
        (145, 0),
        (14, 132),
        (12, 167),
        (146, 0),
        (17, 193),
        (29, 132),
        (96, 176),
        (28, 144),
        (27, 193),
        (140, 0),
        (31, 180),
        (148, 0),
        (27, 192),
        (14, 132),
        (83, 160),
        (18, 137),
        (17, 193),
        (23, 132),
        (13, 165),
        (13, 145),
        (151, 0),
        (147, 0),
        (27, 178),
        (96, 137),
        (19, 193),
        (159, 0),
        (14, 160),
        (25, 148),
        (17, 193),
        (142, 0),
        (16, 180),
        (27, 136),
        (14, 193),
        (224, 0),
        (17, 178),
        (12, 144),
        (224, 0),
        (28, 132),
        (27, 160),
        (13, 141),
        (11, 193),
        (96, 132),
        (27, 165),
        (30, 140),
        (224, 0),
        (146, 0),
        (31, 165),
        (29, 129),
        (96, 192),
        (140, 0),
        (31, 161),
        (24, 145),
        (140, 0),
        (96, 132),
        (27, 165),
        (29, 140),
        (31, 192),
        (154, 0),
        (14, 161),
        (27, 145),
        (140, 0),
        (18, 132),
        (23, 167),
        (96, 140),
        (21, 129),
        (14, 132),
        (17, 165),
        (9, 137),
        (12, 193),
        (155, 0),
        (18, 161),
        (96, 141),
        (27, 192),
        (148, 0),
        (29, 178),
        (23, 133),
        (24, 192),
        (155, 0),
        (10, 180),
        (96, 133),
        (28, 192),
        (14, 132),
        (31, 130),
        (28, 129),
        (18, 193),
        (31, 132),
        (12, 180),
        (13, 144),
        (96, 193),
        (31, 132),
        (96, 160),
        (13, 141),
        (27, 193),
        (18, 132),
        (23, 181),
        (26, 140),
        (27, 193),
        (156, 0),
        (96, 166),
        (79, 141),
        (211, 0),
        (76, 132),
        (77, 160),
        (75, 133),
        (206, 0),
        (182, 0),
        (96, 129),
        (59, 133),
        (191, 0),
        (173, 0),
    ];

    assert!(block_data.len() <= BLOCK_SIZE);

    let mut decoded_block: Vec<u8> = vec![];

    for (i, byte) in block_data.iter().enumerate() {
        let encoding = encoding_table[i];

        decoded_block.push(((((*byte as usize) + encoding.0) ^ encoding.1) % 256) as u8);
    }

    decoded_block
}
