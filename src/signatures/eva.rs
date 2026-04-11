use crate::signatures::common::{
    CONFIDENCE_HIGH, CONFIDENCE_LOW, CONFIDENCE_MEDIUM, SignatureError, SignatureResult,
};
use crate::structures::eva::{EvaTiRecordKind, parse_eva_image};

/// Human readable description
pub const DESCRIPTION: &str = "Fritz!Box EVA kernel image";

/// EVA magic bytes (dual-kernel, primary TI record, secondary TI record)
///
/// The secondary magic is registered to detect isolated secondary-only
/// fragments. Inside a dual-kernel image the scanner will also hit on the
/// embedded secondary magic; that duplicate lands inside the already-validated
/// dual-kernel region and is filtered out by the conflict-resolution pass in
/// `Binwalk::scan`.
pub fn eva_magic() -> Vec<Vec<u8>> {
    vec![
        // DUAL_KERNEL (little-endian 0xFEED9112)
        b"\x12\x91\xed\xfe".to_vec(),
        // TI_AR7 primary (little-endian 0xFEED1281)
        b"\x81\x12\xed\xfe".to_vec(),
        // TI_AR7_2ND secondary (little-endian 0xFEEDB007)
        b"\x07\xb0\xed\xfe".to_vec(),
    ]
}

/// Validates EVA kernel image signatures
pub fn eva_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    let data = file_data.get(offset..).ok_or(SignatureError)?;
    let image = parse_eva_image(data).map_err(|_| SignatureError)?;

    let secondary_checksums_ok = image
        .secondary
        .as_ref()
        .is_none_or(|s| s.checksum_valid && s.lzma.data_checksum_valid);
    let file_signature_ok = image.file_signature.is_none_or(|sig| sig.valid);

    let all_checksums_valid = image.primary.checksum_valid
        && image.primary.lzma.data_checksum_valid
        && secondary_checksums_ok
        && (!image.is_dual_kernel || image.dual_checksum_valid)
        && file_signature_ok;

    // A bad checksum at offset 0 is usually a real-but-modified image; deeper in a file it's more likely a false 4-byte match
    let confidence = if all_checksums_valid {
        CONFIDENCE_HIGH
    } else if offset == 0 {
        CONFIDENCE_MEDIUM
    } else {
        CONFIDENCE_LOW
    };

    let kernel_phrase = if image.is_dual_kernel {
        "dual-kernel"
    } else if image.primary.kind == EvaTiRecordKind::Secondary {
        "secondary-kernel fragment"
    } else {
        "single-kernel"
    };
    let primary_label = match image.primary.kind {
        EvaTiRecordKind::Primary => "primary",
        EvaTiRecordKind::Secondary => "secondary",
    };
    let primary_desc = format!(
        "{} load: {:#X}, entry: {:#X}, compressed: {} bytes, uncompressed: {} bytes",
        primary_label,
        image.primary.load_addr,
        image.primary.entry_addr,
        image.primary.lzma.compressed_len,
        image.primary.lzma.uncompressed_len,
    );
    let secondary_desc = image
        .secondary
        .as_ref()
        .map(|s| {
            format!(
                ", secondary load: {:#X}, entry: {:#X}, compressed: {} bytes, uncompressed: {} bytes",
                s.load_addr, s.entry_addr, s.lzma.compressed_len, s.lzma.uncompressed_len,
            )
        })
        .unwrap_or_default();
    let signature_desc = image
        .file_signature
        .map(|sig| format!(", file signature CRC: {:#010X}", sig.crc))
        .unwrap_or_default();
    let validation_desc = if all_checksums_valid {
        String::new()
    } else {
        let mut failures: Vec<&str> = Vec::new();
        if !image.primary.checksum_valid {
            failures.push("primary TI");
        }
        if !image.primary.lzma.data_checksum_valid {
            failures.push("primary LZMA data");
        }
        if let Some(ref s) = image.secondary {
            if !s.checksum_valid {
                failures.push("secondary TI");
            }
            if !s.lzma.data_checksum_valid {
                failures.push("secondary LZMA data");
            }
        }
        if image.is_dual_kernel && !image.dual_checksum_valid {
            failures.push("dual trailer");
        }
        if image.file_signature.is_some_and(|sig| !sig.valid) {
            failures.push("file signature");
        }
        format!(", checksum validation failed ({})", failures.join(", "))
    };

    Ok(SignatureResult {
        offset,
        size: image.total_size,
        confidence,
        description: format!(
            "{}, {}, {}{}{}{}",
            DESCRIPTION,
            kernel_phrase,
            primary_desc,
            secondary_desc,
            signature_desc,
            validation_desc,
        ),
        ..Default::default()
    })
}
