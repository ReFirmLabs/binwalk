use crate::extractors::common::{Chroot, ExtractionResult, Extractor, ExtractorType};
use crate::structures::lz4l::{find_lz4l_compressed_length, parse_lz4l_header};

/// Defines the internal extractor function for decompressing LZ4L data
pub fn lz4l_extractor() -> Extractor {
    Extractor {
        utility: ExtractorType::Internal(lz4l_decompress),
        ..Default::default()
    }
}

/// Internal extractor for decompressing LZ4L (UNISOC NV-storage wrapper) data
///
/// Re-parses the header and re-finds the exact compressed length (see
/// `find_lz4l_compressed_length`), then decompresses that exact slice.
pub fn lz4l_decompress(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&str>,
) -> ExtractionResult {
    const OUTPUT_FILE_NAME: &str = "decompressed.bin";
    const HEADER_SIZE: usize = 8;

    let mut result = ExtractionResult {
        ..Default::default()
    };

    let header = match parse_lz4l_header(&file_data[offset..]) {
        Ok(header) => header,
        Err(_) => return result,
    };

    let available = match file_data.get(offset + HEADER_SIZE..) {
        Some(data) => data,
        None => return result,
    };

    let compressed_len = match find_lz4l_compressed_length(available, header.uncompressed_size) {
        Some(len) => len,
        None => return result,
    };

    let decompressed = match lz4::block::decompress(
        &available[..compressed_len],
        Some(header.uncompressed_size as i32),
    ) {
        Ok(data) => data,
        Err(_) => return result,
    };

    if decompressed.len() != header.uncompressed_size {
        return result;
    }

    if output_directory.is_some() {
        let chroot = Chroot::new(output_directory);
        if !chroot.create_file(OUTPUT_FILE_NAME, &decompressed) {
            return result;
        }
    }

    result.size = Some(HEADER_SIZE + compressed_len);
    result.success = true;
    result
}
