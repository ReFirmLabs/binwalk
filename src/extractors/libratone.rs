use crate::extractors::common::{Chroot, ExtractionResult, Extractor, ExtractorType};
use crate::signatures::libratone::deobfuscate;
use crate::signatures::zip::find_zip_eof;

pub fn libratone_extractor() -> Extractor {
    Extractor {
        utility: ExtractorType::Internal(extract_libratone),
        ..Default::default()
    }
}

pub fn extract_libratone(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&str>,
) -> ExtractionResult {
    const OUTFILE_NAME: &str = "libratone.zip";
    const PAYLOAD_MAGIC: &[u8] = b"PJ\x01\x01";
    const MAX_HEADER_LEN: usize = 128;

    let mut result = ExtractionResult {
        ..Default::default()
    };

    if offset != 0 {
        return result;
    }

    let search_end = std::cmp::min(file_data.len(), MAX_HEADER_LEN);
    let header_window = match file_data.get(offset..search_end) {
        Some(w) => w,
        None => return result,
    };
    let payload_rel = match header_window
        .windows(PAYLOAD_MAGIC.len())
        .position(|w| w == PAYLOAD_MAGIC)
    {
        Some(p) => p,
        None => return result,
    };
    let payload_offset = offset + payload_rel;

    let payload = match file_data.get(payload_offset..) {
        Some(p) => p,
        None => return result,
    };
    let decoded = deobfuscate(payload);

    if let Ok(zip_info) = find_zip_eof(&decoded, 0) {
        result.size = Some(payload_rel + zip_info.eof);
        result.success = true;

        if output_directory.is_some() {
            let chroot = Chroot::new(output_directory);
            match decoded.get(0..zip_info.eof) {
                Some(zip_data) => {
                    result.success = chroot.create_file(OUTFILE_NAME, zip_data);
                }
                None => {
                    result.success = false;
                }
            }
        }
    }

    result
}
