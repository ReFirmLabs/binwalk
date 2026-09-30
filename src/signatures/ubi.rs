use crate::signatures::common::{
    CONFIDENCE_HIGH, CONFIDENCE_MEDIUM, SignatureError, SignatureResult,
};
use crate::structures::ubi::{
    parse_ubi_ec_header, parse_ubi_superblock_header, parse_ubi_volume_header,
};
use aho_corasick::AhoCorasick;
use std::collections::HashMap;

/// Human readable desciptions
pub const UBI_FS_DESCRIPTION: &str = "UBIFS image";
pub const UBI_IMAGE_DESCRIPTION: &str = "UBI image";

/// Erase block magic bytes; header version is assumed to be 1
pub fn ubi_magic() -> Vec<Vec<u8>> {
    vec![b"UBI#\x01".to_vec()]
}

/// UBI node magic; this matches *any* UBI node, but ubifs_parser ensures that only superblock nodes are reported
pub fn ubifs_magic() -> Vec<Vec<u8>> {
    vec![b"\x31\x18\x10\x06".to_vec()]
}

/// Validates a UBIFS signature
pub fn ubifs_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Success return value
    let mut result = SignatureResult {
        offset,
        description: UBI_FS_DESCRIPTION.to_string(),
        confidence: CONFIDENCE_HIGH,
        ..Default::default()
    };

    // Parse the UBIFS superblock header
    if let Ok(sb_header) = parse_ubi_superblock_header(&file_data[offset..]) {
        // Image size is the number of logical erase blocks times the size of each logical erase block
        let image_size: usize = sb_header.leb_count.saturating_mul(sb_header.leb_size);
        result.description = format!("{}, total size: {} bytes", result.description, image_size);

        // A signature whose size runs past EOF is discarded as invalid; report a truncated image
        // as an unknown size instead, so that what data there is can still be extracted
        if image_size > (file_data.len() - offset) {
            result.description = format!("{} (truncated)", result.description);
        } else {
            result.size = image_size;
        }

        // Images with a corrupt or missing header checksum are still reported, but with less confidence
        if !sb_header.crc_valid {
            result.confidence = CONFIDENCE_MEDIUM;
            result.description = format!("{}, invalid header checksum", result.description);
        }

        return Ok(result);
    }

    Err(SignatureError)
}

/// Validates a UBI signature
pub fn ubi_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Success return value
    let mut result = SignatureResult {
        offset,
        description: UBI_IMAGE_DESCRIPTION.to_string(),
        confidence: CONFIDENCE_HIGH,
        ..Default::default()
    };

    // Parse the UBI header
    if let Ok(ubi_header) = parse_ubi_ec_header(&file_data[offset..]) {
        let data_offset: usize = offset + ubi_header.data_offset;
        let volume_offset: usize = offset + ubi_header.volume_id_offset;

        // Sanity check the reported volume and data offsets
        if file_data.len() > data_offset && file_data.len() > volume_offset {
            // Get the size of the UBI image
            if let Ok((image_size, block_crcs_valid)) = get_ubi_image_size(&file_data[offset..]) {
                result.size = image_size;
                result.description = format!(
                    "{}, version: {}, image size: {} bytes",
                    result.description, ubi_header.version, result.size
                );

                // Images with corrupt or missing header checksums are still reported, but with less confidence
                if !ubi_header.crc_valid || !block_crcs_valid {
                    result.confidence = CONFIDENCE_MEDIUM;
                    result.description =
                        format!("{}, invalid header checksums", result.description);
                }

                return Ok(result);
            }
        }
    }

    Err(SignatureError)
}

/// Determines the LEB size and returns the size of the UBI image, along with false if any of the
/// volume headers that make up the image had a corrupt or missing checksum
fn get_ubi_image_size(ubi_data: &[u8]) -> Result<(usize, bool), SignatureError> {
    let mut leb_size: usize = 0;
    let mut block_count: usize = 0;
    let mut crcs_valid: bool = true;
    let mut best_leb_match_count: usize = 0;
    let mut previous_volume_offset: usize = 0;
    let mut possible_leb_sizes: HashMap<usize, usize> = HashMap::new();

    // Volume magic bytes, version is assumed to be 1
    let ubi_vol_magic = vec![b"UBI!\x01"];

    let grep = AhoCorasick::new(ubi_vol_magic).unwrap();

    // grep for all volume header magic bytes
    for magic_match in grep.find_overlapping_iter(ubi_data) {
        // Offset in the UBI image where this magic match was found
        let this_volume_offset: usize = magic_match.start();

        // Parse the volume header
        if let Ok(volume_header) = parse_ubi_volume_header(&ubi_data[this_volume_offset..]) {
            // Header looks valid, increment the block count
            block_count += 1;
            crcs_valid &= volume_header.crc_valid;

            // If there was a previous UBI volume header identified, calculate the leb size as the distance between the two volume header
            if previous_volume_offset != 0 {
                let this_leb_size = this_volume_offset - previous_volume_offset;

                // Keep track of the calculated leb size, and how many times each possible leb size was found
                if possible_leb_sizes.contains_key(&this_leb_size) {
                    possible_leb_sizes
                        .insert(this_leb_size, possible_leb_sizes[&this_leb_size] + 1);
                } else {
                    possible_leb_sizes.insert(this_leb_size, 1);
                }
            }

            previous_volume_offset = this_volume_offset;
        }
    }

    // Pick the most common leb size
    for (leb_candidate_size, leb_candidate_count) in possible_leb_sizes.iter() {
        if *leb_candidate_count > best_leb_match_count {
            leb_size = *leb_candidate_size;
            best_leb_match_count = *leb_candidate_count;
        }
    }

    // Image size is leb size times the number of blocks
    if leb_size != 0 && block_count != 0 {
        return Ok((block_count.saturating_mul(leb_size), crcs_valid));
    }

    Err(SignatureError)
}
