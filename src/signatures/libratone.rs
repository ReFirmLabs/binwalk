use crate::signatures::common::{CONFIDENCE_HIGH, SignatureError, SignatureResult};
use crate::signatures::zip::find_zip_eof;

pub const DESCRIPTION: &str = "Libratone firmware update";

const HEADER_MAGIC: &[u8] = b"FFAA\n";
const PAYLOAD_MAGIC: &[u8] = b"PJ\x01\x01";
const MAX_HEADER_LEN: usize = 128;

pub fn libratone_magic() -> Vec<Vec<u8>> {
    vec![HEADER_MAGIC.to_vec()]
}

pub fn deobfuscate(payload: &[u8]) -> Vec<u8> {
    payload
        .iter()
        .enumerate()
        .map(|(i, b)| b.wrapping_add((i & 0x0F) as u8))
        .collect()
}

pub fn libratone_parser(
    file_data: &[u8],
    offset: usize,
) -> Result<SignatureResult, SignatureError> {
    if offset != 0 {
        return Err(SignatureError);
    }

    let search_end = std::cmp::min(file_data.len(), MAX_HEADER_LEN);
    let header_window = file_data.get(offset..search_end).ok_or(SignatureError)?;
    let payload_rel = find_subsequence(header_window, PAYLOAD_MAGIC).ok_or(SignatureError)?;
    let payload_offset = offset + payload_rel;

    let header_text = file_data
        .get(offset..payload_offset)
        .ok_or(SignatureError)?;
    let fields: Vec<&[u8]> = header_text.split(|&b| b == b'\n').collect();

    if fields.len() < 4 {
        return Err(SignatureError);
    }

    if fields[0] != b"FFAA" || fields[fields.len() - 2] != b"FFAA" {
        return Err(SignatureError);
    }

    for field in &fields {
        if field.iter().any(|&b| b != 0 && !(0x20..=0x7e).contains(&b)) {
            return Err(SignatureError);
        }
    }

    let inner = &fields[1..fields.len() - 2];
    let build = inner
        .last()
        .map(|b| String::from_utf8_lossy(b).to_string())
        .unwrap_or_default();
    let versions: Vec<String> = inner
        .iter()
        .take(inner.len().saturating_sub(1))
        .map(|b| String::from_utf8_lossy(b).to_string())
        .collect();

    let mut size = 0;
    if let Some(payload) = file_data.get(payload_offset..) {
        let decoded = deobfuscate(payload);
        if let Ok(zip_info) = find_zip_eof(&decoded, 0) {
            size = payload_rel + zip_info.eof;
        }
    }

    Ok(SignatureResult {
        offset,
        size,
        confidence: CONFIDENCE_HIGH,
        description: format!(
            "{}, build {}, component versions: {}",
            DESCRIPTION,
            build,
            versions.join(", ")
        ),
        ..Default::default()
    })
}

fn find_subsequence(haystack: &[u8], needle: &[u8]) -> Option<usize> {
    if needle.is_empty() || haystack.len() < needle.len() {
        return None;
    }
    haystack.windows(needle.len()).position(|w| w == needle)
}
