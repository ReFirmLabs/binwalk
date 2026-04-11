use crate::extractors::common::{Chroot, ExtractionResult, Extractor, ExtractorType};
use crate::structures::eva::{
    EVA_LZMA_HEADER_SIZE, EVA_LZMA_STREAM_HEADER, EvaTiRecord, EvaTiRecordKind, TI_HEADER_SIZE,
    parse_eva_image,
};

/// Defines the internal extractor for Fritz!Box EVA kernel images
pub fn eva_extractor() -> Extractor {
    Extractor {
        utility: ExtractorType::Internal(extract_eva),
        ..Default::default()
    }
}

/// Internal EVA kernel image extractor
pub fn extract_eva(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&str>,
) -> ExtractionResult {
    let mut result = ExtractionResult::default();

    let Some(data) = file_data.get(offset..) else {
        return result;
    };
    let Ok(image) = parse_eva_image(data) else {
        return result;
    };

    // Refuse to carve garbage even if the signature parser let a weak match through
    if !image.primary.checksum_valid || !image.primary.lzma.data_checksum_valid {
        return result;
    }
    if let Some(ref secondary) = image.secondary
        && (!secondary.checksum_valid || !secondary.lzma.data_checksum_valid)
    {
        return result;
    }

    let Some(primary_lzma) = reconstruct_lzma_alone(data, &image.primary) else {
        return result;
    };
    let secondary_lzma = match image.secondary.as_ref() {
        Some(secondary) => match reconstruct_lzma_alone(data, secondary) {
            Some(bytes) => Some(bytes),
            None => return result,
        },
        None => None,
    };

    let primary_file_name = match image.primary.kind {
        EvaTiRecordKind::Primary => "kernel.lzma",
        EvaTiRecordKind::Secondary => "kernel_2nd.lzma",
    };

    if output_directory.is_some() {
        let chroot = Chroot::new(output_directory);
        if !chroot.create_file(primary_file_name, &primary_lzma) {
            return result;
        }
        if let Some(ref bytes) = secondary_lzma
            && !chroot.create_file("kernel_2nd.lzma", bytes)
        {
            return result;
        }
    }

    result.success = true;
    result.size = Some(image.total_size);
    result
}

/// Reconstruct a standard LZMA alone stream from an EVA TI record
///
/// Standard LZMA alone format:
/// ```text
///   [properties:        1 byte]
///   [dict_size:         4 bytes, little-endian]
///   [uncompressed_size: 8 bytes, little-endian]  (upper 4 bytes zero-padded)
///   [compressed_data:   compressed_len bytes]
/// ```
///
/// The 3 "unknown" padding bytes from the EVA stream header are dropped
fn reconstruct_lzma_alone(image_data: &[u8], record: &EvaTiRecord) -> Option<Vec<u8>> {
    let compressed_data_offset =
        record.header_offset + TI_HEADER_SIZE + EVA_LZMA_HEADER_SIZE + EVA_LZMA_STREAM_HEADER;
    let compressed_data_end = compressed_data_offset.checked_add(record.lzma.compressed_len)?;
    let compressed_data = image_data.get(compressed_data_offset..compressed_data_end)?;

    let mut out = Vec::with_capacity(13 + compressed_data.len());
    out.push(record.lzma.properties);
    out.extend_from_slice(&record.lzma.dict_size.to_le_bytes());
    out.extend_from_slice(&(record.lzma.uncompressed_len as u64).to_le_bytes());
    out.extend_from_slice(compressed_data);
    Some(out)
}
