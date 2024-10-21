use crate::extractors::common::{ExtractionResult, Extractor, ExtractorType};
use crate::extractors::lzma::lzma_decompress;

/// Defines the internal extractor for Arcadyn Obfuscated LZMA
pub fn obfuscated_lzma_extractor() -> Extractor {
    Extractor {
        utility: ExtractorType::Internal(extract_obfuscated_lzma),
        ..Default::default()
    }
}

/// Internal extractor for Arcadyn Obfuscated LZMA
pub fn extract_obfuscated_lzma(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&String>,
) -> ExtractionResult {
    const LZMA_DATA_OFFSET: usize = 4;
    const MIN_DATA_SIZE: usize = 0x100;
    const MAX_DATA_SIZE: usize = 0x1B0000;

    let mut result = ExtractionResult {
        ..Default::default()
    };
    let available_data: usize = file_data.len() - offset;

    // Sanity check data size
    if available_data <= MAX_DATA_SIZE && available_data > MIN_DATA_SIZE {
        // De-obfuscate the LZMA data
        let deobfuscated_data = arcadyan_deobfuscator(&file_data[offset..]);

        // Do a decompression on the LZMA data (actual LZMA data starts 4 bytes into the deobfuscated data)
        result = lzma_decompress(&deobfuscated_data, LZMA_DATA_OFFSET, output_directory);
    }

    result
}

fn arcadyan_deobfuscator(obfuscated_data: &[u8]) -> Vec<u8> {
    const BLOCK_SIZE: usize = 32;

    const P1_START: usize = 0;
    const P1_END: usize = 4;

    const BLOCK1_START: usize = P1_END;
    const BLOCK1_END: usize = BLOCK1_START + BLOCK_SIZE;

    const P2_START: usize = BLOCK1_END;
    const P2_END: usize = 0x68;

    const BLOCK2_START: usize = P2_END;
    const BLOCK2_END: usize = BLOCK2_START + BLOCK_SIZE;

    const P3_START: usize = BLOCK2_END;

    let mut deobfuscated_data: Vec<u8> = vec![];

    // Get the "parts" and "blocks" of the obfuscated header
    let p1 = obfuscated_data[P1_START..P1_END].to_vec();
    let b1 = obfuscated_data[BLOCK1_START..BLOCK1_END].to_vec();
    let p2 = obfuscated_data[P2_START..P2_END].to_vec();
    let b2 = obfuscated_data[BLOCK2_START..BLOCK2_END].to_vec();
    let p3 = obfuscated_data[P3_START..].to_vec();

    // Swap "block1" and "block2"
    deobfuscated_data.extend(p1);
    deobfuscated_data.extend(b2);
    deobfuscated_data.extend(p2);
    deobfuscated_data.extend(b1);
    deobfuscated_data.extend(p3);

    // Nibble swap each byte in what is now "block1"
    for swapped_byte in deobfuscated_data
        .iter_mut()
        .take(BLOCK1_END)
        .skip(BLOCK1_START)
    {
        *swapped_byte = ((*swapped_byte & 0x0F) << 4) + ((*swapped_byte & 0xF0) >> 4);
    }

    let mut i: usize = BLOCK1_START;

    // Byte swap each byte in what is now "block1"
    while i < BLOCK1_END {
        let b1 = deobfuscated_data[i];
        let b2 = deobfuscated_data[i + 1];
        deobfuscated_data[i] = b2;
        deobfuscated_data[i + 1] = b1;
        i += 2;
    }

    deobfuscated_data
}
