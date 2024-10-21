use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_HIGH};
use crate::structures::dmg::parse_dmg_footer;
use aho_corasick::AhoCorasick;

/// Human readable description
pub const DESCRIPTION: &str = "Apple Disk iMaGe";

/// 4-byte magic, 4-byte version (v4), 4-byte structure size (0x0200).
///  This is actually the magic bytes of the DMG footer, there is no standard header format.
pub fn dmg_magic() -> Vec<Vec<u8>> {
    vec![b"koly\x00\x00\x00\x04\x00\x00\x02\x00".to_vec()]
}

/// Validates the DMG footer
pub fn dmg_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Confidence is set to HIGH + 1 to ensure this overrides other signatures.
    // DMG's typically start with compressed data, and the file should be treated
    // as a DMG, not just compressed data.
    let mut result = SignatureResult {
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_HIGH + 1,
        ..Default::default()
    };

    // Parse the DMG footer
    if let Ok(dmg_footer) = parse_dmg_footer(&file_data[offset..]) {
        /*
         * DMG files have the following layout:
         *
         *      [ image data ]  [ xml data ]  [ footer ]
         *
         * We can only signature reliably on the footer, which does contain the offsets and sizes of the image data and xml data.
         * In theory, this would allow us to calculate the starting offset, and size, of the DMG image.
         *
         * In practice, signed DMG files have additional data between the XML and the footer. This extra data appears to
         * be related to signing certificates and is variable in length, making the above theoretical calculations of the DMG offset
         * and size invalid.
         *
         * Instead, we have to search the file data for the XML property, then the correct offset can be calculated.
         */

        // Make sure the length of image data and length of XML data are sane
        if (dmg_footer.data_length + dmg_footer.xml_length) <= offset {
            // Locate the XML data
            if let Some(xml_offset) = find_xml_property_list(file_data) {
                // Make sure the XML data comes after the image data
                if xml_offset >= dmg_footer.data_length {
                    // Report the result
                    result.size = offset + dmg_footer.footer_size;
                    result.offset = xml_offset - dmg_footer.data_length;
                    result.description =
                        format!("{}, total size: {} bytes", result.description, result.size);
                    return Ok(result);
                }
            }
        }
    }

    Err(SignatureError)
}

fn find_xml_property_list(file_data: &[u8]) -> Option<usize> {
    // XML data should start with this string
    const XML_SIGNATURE: &str = "<?xml";
    const MIN_XML_LENGTH: usize = 1024;
    const BLKX_KEY: &str = "<key>blkx</key>";

    let grep = AhoCorasick::new(vec![XML_SIGNATURE]).unwrap();

    for xml_match in grep.find_overlapping_iter(file_data) {
        let xml_start = xml_match.start();
        let xml_end = xml_start + MIN_XML_LENGTH;

        if let Some(xml_data) = file_data.get(xml_start..xml_end) {
            if let Ok(xml_string) = String::from_utf8(xml_data.to_vec()) {
                if xml_string.contains(BLKX_KEY) {
                    return Some(xml_start);
                }
            }
        }
    }

    None
}
