use crate::extractors::common::{
    Chroot, Extractor, ExtractionResult, ExtractorType,
};
use std::process::Command;

const JZLZMA_SCRIPT: &str = include_str!("../../scripts/jzlzma/jzlzma_decompress.py");
const JZLZMA_SCRIPT_NAME: &str = "jzlzma_decompress.py";
const DECOMPRESSED_NAME: &str = "decompressed.bin";

/// Defines an internal extractor for jzlzma data
pub fn jzlzma_extractor() -> Extractor {
    Extractor {
        utility: ExtractorType::Internal(jzlzma_decompress),
        ..Default::default()
    }
}

/// Internal extractor: writes the embedded Python decompressor, runs it on the
/// carved jzlzma data, and collects the decompressed output.
pub fn jzlzma_decompress(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&str>,
) -> ExtractionResult {
    let mut result = ExtractionResult {
        ..Default::default()
    };

    // Dry run (signature validation): just report that the data looks valid.
    // The signature parser already validated the header and determined the size.
    if output_directory.is_none() {
        result.success = true;
        return result;
    }

    let out_dir = output_directory.unwrap();
    let chroot = Chroot::new(Some(out_dir));

    // Write the embedded Python script to the output directory
    if !chroot.create_file(JZLZMA_SCRIPT_NAME, JZLZMA_SCRIPT.as_bytes()) {
        return result;
    }

    // Carve the jzlzma data (wrapper header + compressed stream)
    // mark_rootfs_lzma wrapper has magic at bytes 4-7, so include the 4-byte preamble
    let carved_name = "carved.jzlzma";
    let carve_start = if offset >= 4 { offset - 4 } else { offset };
    if !chroot.carve_file(carved_name, file_data, carve_start, file_data.len() - carve_start) {
        return result;
    }

    // Build paths
    let script_path = chroot.chrooted_path(JZLZMA_SCRIPT_NAME);
    let carved_path = chroot.chrooted_path(carved_name);
    let decompressed_path = chroot.chrooted_path(DECOMPRESSED_NAME);

    // Run python3 <script> <carved> <output>
    match Command::new("python3")
        .arg(&script_path)
        .arg(&carved_path)
        .arg(&decompressed_path)
        .status()
    {
        Ok(status) => {
            if status.success() {
                result.size = Some(std::fs::metadata(&decompressed_path)
                    .map(|m| m.len() as usize)
                    .unwrap_or(0));
                result.success = true;
            }
        }
        Err(_) => {}
    }

    // Clean up carved and script files
    let _ = std::fs::remove_file(&carved_path);
    let _ = std::fs::remove_file(&script_path);

    result
}
