use crate::common::{crc32, eva_file_signature_crc32};
use crate::structures::common::{self, StructureError};

/// Outer dual-kernel container magic
pub const DUAL_KERNEL_MAGIC: u32 = 0xFEED9112;

/// Primary TI record magic
pub const TI_AR7_MAGIC: u32 = 0xFEED1281;

/// Secondary TI record magic
pub const TI_AR7_2ND_MAGIC: u32 = 0xFEEDB007;

/// EVA LZMA payload type marker
pub const EVA_LZMA_TYPE_MAGIC: u32 = 0x075A0201;

/// Trailing file signature magic
pub const FILE_SIGNATURE_MAGIC: u32 = 0xC453DE23;

/// Size of a TI record header (magic + payload_length + load_addr)
pub const TI_HEADER_SIZE: usize = 12;

/// Size of a TI record trailer (checksum + zero + entry_addr)
pub const TI_TRAILER_SIZE: usize = 12;

/// Size of the EVA LZMA header (type + compressed_len + uncompressed_len + data_checksum)
pub const EVA_LZMA_HEADER_SIZE: usize = 16;

/// Size of the EVA LZMA stream header (properties + dict_size + 3 padding bytes)
pub const EVA_LZMA_STREAM_HEADER: usize = 8;

/// Size of the trailing file signature (magic + crc)
pub const FILE_SIGNATURE_SIZE: usize = 8;

// Max bytes to scan for a trailing file signature after the last TI trailer
const FILE_SIGNATURE_SCAN_WINDOW: usize = 4096;

/// Parsed EVA LZMA payload (16-byte header + 8-byte stream header, followed by compressed data)
#[derive(Debug, Default, Clone)]
pub struct EvaLzmaPayload {
    pub compressed_len: usize,
    pub uncompressed_len: usize,
    pub data_checksum_valid: bool,
    pub properties: u8,
    pub dict_size: u32,
}

/// Which TI record magic matched this record
#[derive(Debug, Default, Clone, Copy, PartialEq, Eq)]
pub enum EvaTiRecordKind {
    #[default]
    Primary,
    Secondary,
}

/// Parsed TI record (header + EVA LZMA payload + trailer)
#[derive(Debug, Default, Clone)]
pub struct EvaTiRecord {
    pub kind: EvaTiRecordKind,
    pub load_addr: u32,
    pub checksum_valid: bool,
    pub entry_addr: u32,
    pub lzma: EvaLzmaPayload,
    pub header_offset: usize,
    pub total_size: usize,
}

/// Located trailing EVA file signature
#[derive(Debug, Default, Clone, Copy)]
pub struct EvaFileSignature {
    pub crc: u32,
    pub valid: bool,
    /// Absolute end offset of the signature (i.e. where the EVA image ends)
    pub end_offset: usize,
}

/// Parsed EVA kernel image
#[derive(Debug, Default, Clone)]
pub struct EvaImage {
    pub is_dual_kernel: bool,
    pub primary: EvaTiRecord,
    pub secondary: Option<EvaTiRecord>,
    pub dual_checksum_valid: bool,
    pub file_signature: Option<EvaFileSignature>,
    pub total_size: usize,
}

/// Parse a Fritz!Box EVA kernel image
pub fn parse_eva_image(data: &[u8]) -> Result<EvaImage, StructureError> {
    if data.len() < TI_HEADER_SIZE {
        return Err(StructureError);
    }

    let header = common::parse(data, &vec![("magic", "u32")], "little")?;
    match header["magic"] as u32 {
        DUAL_KERNEL_MAGIC => parse_dual_kernel_image(data),
        TI_AR7_MAGIC => parse_single_kernel_image(data, TI_AR7_MAGIC),
        TI_AR7_2ND_MAGIC => parse_single_kernel_image(data, TI_AR7_2ND_MAGIC),
        _ => Err(StructureError),
    }
}

/// Parse a dual-kernel EVA image
fn parse_dual_kernel_image(data: &[u8]) -> Result<EvaImage, StructureError> {
    let dual_header_structure = vec![
        ("magic", "u32"),
        ("payload_length", "u32"),
        ("load_addr", "u32"),
    ];

    let dual_header = common::parse(data, &dual_header_structure, "little")?;
    let dual_payload_length = dual_header["payload_length"];
    let dual_payload_length_u32 = u32::try_from(dual_payload_length).map_err(|_| StructureError)?;
    let dual_load_addr = dual_header["load_addr"] as u32;

    let primary = parse_ti_record(data, TI_HEADER_SIZE, TI_AR7_MAGIC)?;
    let after_primary = primary.header_offset + primary.total_size;

    // Secondary TI record starts at the next 4-byte aligned offset
    let aligned_secondary_offset = align_up(after_primary, 4);
    let secondary = parse_ti_record(data, aligned_secondary_offset, TI_AR7_2ND_MAGIC)?;
    let after_secondary = secondary.header_offset + secondary.total_size;

    let dual_trailer_offset = TI_HEADER_SIZE
        .checked_add(dual_payload_length)
        .ok_or(StructureError)?;
    if dual_trailer_offset < after_secondary {
        return Err(StructureError);
    }
    let dual_trailer_end = dual_trailer_offset
        .checked_add(TI_TRAILER_SIZE)
        .ok_or(StructureError)?;
    if data.len() < dual_trailer_end {
        return Err(StructureError);
    }

    let dual_trailer_data = data
        .get(dual_trailer_offset..dual_trailer_end)
        .ok_or(StructureError)?;
    let dual_trailer_structure = vec![("checksum", "u32"), ("zero", "u32"), ("entry_addr", "u32")];
    let dual_trailer = common::parse(dual_trailer_data, &dual_trailer_structure, "little")?;
    if dual_trailer["zero"] != 0 {
        return Err(StructureError);
    }

    // Dual checksum covers every byte between the dual header and the dual trailer
    let dual_payload = data
        .get(TI_HEADER_SIZE..dual_trailer_offset)
        .ok_or(StructureError)?;
    let expected_dual_checksum =
        calculate_ti_checksum(dual_payload_length_u32, dual_load_addr, dual_payload);
    let dual_checksum_valid = dual_trailer["checksum"] as u32 == expected_dual_checksum;

    let file_signature = detect_file_signature(data, dual_trailer_end);
    let total_size = file_signature
        .map(|sig| sig.end_offset)
        .unwrap_or(dual_trailer_end);

    Ok(EvaImage {
        is_dual_kernel: true,
        primary,
        secondary: Some(secondary),
        dual_checksum_valid,
        file_signature,
        total_size,
    })
}

/// Parse a single-kernel EVA image, or an isolated secondary TI record fragment
fn parse_single_kernel_image(data: &[u8], expected_magic: u32) -> Result<EvaImage, StructureError> {
    let primary = parse_ti_record(data, 0, expected_magic)?;
    let content_end = primary.total_size;

    // Secondary-only fragments never carry a trailing file signature
    let file_signature = if primary.kind == EvaTiRecordKind::Primary {
        detect_file_signature(data, content_end)
    } else {
        None
    };
    let total_size = file_signature
        .map(|sig| sig.end_offset)
        .unwrap_or(content_end);

    Ok(EvaImage {
        is_dual_kernel: false,
        primary,
        secondary: None,
        file_signature,
        total_size,
        ..Default::default()
    })
}

/// Parse a TI record at the given offset
fn parse_ti_record(
    data: &[u8],
    offset: usize,
    expected_magic: u32,
) -> Result<EvaTiRecord, StructureError> {
    let header_end = offset.checked_add(TI_HEADER_SIZE).ok_or(StructureError)?;
    let header_data = data.get(offset..header_end).ok_or(StructureError)?;

    let header_structure = vec![
        ("magic", "u32"),
        ("payload_length", "u32"),
        ("load_addr", "u32"),
    ];
    let header = common::parse(header_data, &header_structure, "little")?;
    if header["magic"] as u32 != expected_magic {
        return Err(StructureError);
    }
    let payload_length = header["payload_length"];
    let payload_length_u32 = u32::try_from(payload_length).map_err(|_| StructureError)?;
    let load_addr = header["load_addr"] as u32;

    let payload_start = header_end;
    let payload_end = payload_start
        .checked_add(payload_length)
        .ok_or(StructureError)?;
    let trailer_end = payload_end
        .checked_add(TI_TRAILER_SIZE)
        .ok_or(StructureError)?;
    if data.len() < trailer_end {
        return Err(StructureError);
    }

    let payload = data.get(payload_start..payload_end).ok_or(StructureError)?;
    let lzma = parse_eva_lzma_payload(payload)?;

    let trailer_data = data.get(payload_end..trailer_end).ok_or(StructureError)?;
    let trailer_structure = vec![("checksum", "u32"), ("zero", "u32"), ("entry_addr", "u32")];
    let trailer = common::parse(trailer_data, &trailer_structure, "little")?;
    if trailer["zero"] != 0 {
        return Err(StructureError);
    }
    let entry_addr = trailer["entry_addr"] as u32;

    let expected_checksum = calculate_ti_checksum(payload_length_u32, load_addr, payload);
    let checksum_valid = trailer["checksum"] as u32 == expected_checksum;

    let kind = match expected_magic {
        TI_AR7_MAGIC => EvaTiRecordKind::Primary,
        TI_AR7_2ND_MAGIC => EvaTiRecordKind::Secondary,
        _ => return Err(StructureError),
    };

    Ok(EvaTiRecord {
        kind,
        load_addr,
        checksum_valid,
        entry_addr,
        lzma,
        header_offset: offset,
        total_size: trailer_end - offset,
    })
}

/// Parse an EVA LZMA payload (16-byte header + 8-byte stream header + compressed data)
fn parse_eva_lzma_payload(payload: &[u8]) -> Result<EvaLzmaPayload, StructureError> {
    if payload.len() < EVA_LZMA_HEADER_SIZE + EVA_LZMA_STREAM_HEADER {
        return Err(StructureError);
    }

    let lzma_header_structure = vec![
        ("type", "u32"),
        ("compressed_len", "u32"),
        ("uncompressed_len", "u32"),
        ("data_checksum", "u32"),
    ];
    let lzma_header = common::parse(payload, &lzma_header_structure, "little")?;
    if lzma_header["type"] as u32 != EVA_LZMA_TYPE_MAGIC {
        return Err(StructureError);
    }
    let compressed_len = lzma_header["compressed_len"];
    let uncompressed_len = lzma_header["uncompressed_len"];
    let stored_data_checksum = lzma_header["data_checksum"] as u32;

    // Stream header: properties(1) + dict_size(4) + unknown(3)
    let stream_header = payload
        .get(EVA_LZMA_HEADER_SIZE..EVA_LZMA_HEADER_SIZE + EVA_LZMA_STREAM_HEADER)
        .ok_or(StructureError)?;
    let properties = stream_header[0];
    let dict_size = u32::from_le_bytes([
        stream_header[1],
        stream_header[2],
        stream_header[3],
        stream_header[4],
    ]);

    // Compressed data lives immediately after the stream header
    let data_start = EVA_LZMA_HEADER_SIZE + EVA_LZMA_STREAM_HEADER;
    let data_end = data_start
        .checked_add(compressed_len)
        .ok_or(StructureError)?;
    if payload.len() < data_end {
        return Err(StructureError);
    }
    let compressed_data = payload.get(data_start..data_end).ok_or(StructureError)?;

    let data_checksum_valid = crc32(compressed_data) == stored_data_checksum;

    Ok(EvaLzmaPayload {
        compressed_len,
        uncompressed_len,
        data_checksum_valid,
        properties,
        dict_size,
    })
}

/// Two's complement additive checksum: `(payload_length + load_addr + sum_of_payload_bytes + checksum) ≡ 0 (mod 2^32)`
fn calculate_ti_checksum(payload_length: u32, load_addr: u32, payload: &[u8]) -> u32 {
    let byte_sum: u32 = payload
        .iter()
        .fold(0u32, |acc, &b| acc.wrapping_add(u32::from(b)));
    let total = payload_length
        .wrapping_add(load_addr)
        .wrapping_add(byte_sum);
    (!total).wrapping_add(1)
}

/// Round `n` up to the next multiple of `alignment`
fn align_up(n: usize, alignment: usize) -> usize {
    (n + alignment - 1) & !(alignment - 1)
}

/// Locate and validate a trailing EVA file signature within a bounded window
/// after `content_end`. The window is capped so an embedded EVA match inside a
/// larger firmware cannot accidentally over-extend its reported size by
/// matching random trailing bytes.
fn detect_file_signature(data: &[u8], content_end: usize) -> Option<EvaFileSignature> {
    let try_offset = |candidate: usize| -> Option<EvaFileSignature> {
        let sig_end = candidate.checked_add(FILE_SIGNATURE_SIZE)?;
        let bytes: &[u8; FILE_SIGNATURE_SIZE] = data.get(candidate..sig_end)?.try_into().ok()?;
        let magic = u32::from_le_bytes(bytes[0..4].try_into().unwrap());
        if magic != FILE_SIGNATURE_MAGIC {
            return None;
        }
        let crc = u32::from_le_bytes(bytes[4..8].try_into().unwrap());
        // CRC input is everything before the 8-byte signature
        let crc_input = data.get(0..candidate)?;
        let expected_crc = eva_file_signature_crc32(crc_input);
        Some(EvaFileSignature {
            crc,
            valid: crc == expected_crc,
            end_offset: sig_end,
        })
    };

    // Forward scan at 4-byte aligned offsets within the bounded window.
    let scan_start = align_up(content_end, 4);
    let scan_end = std::cmp::min(
        data.len(),
        content_end.saturating_add(FILE_SIGNATURE_SCAN_WINDOW),
    );
    let mut off = scan_start;
    while off + FILE_SIGNATURE_SIZE <= scan_end {
        if let Some(result) = try_offset(off) {
            return Some(result);
        }
        off += 4;
    }

    None
}
