use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_HIGH};
use crate::structures::dmg::parse_dmg_footer;

/// Human readable description
pub const DESCRIPTION: &str = "Apple Disk iMaGe";

/// 4-byte magic, 4-byte version (v4), 4-byte structure size (0x0200).
///  This is actually the magic bytes of the DMG footer, there is no standard header format.
pub fn dmg_magic() -> Vec<Vec<u8>> {
    return vec![b"koly\x00\x00\x00\x04\x00\x00\x02\x00".to_vec()];
}

/// Validates the DMG footer
pub fn dmg_parser(file_data: &Vec<u8>, offset: usize) -> Result<SignatureResult, SignatureError> {
    // XML data should start with this string
    const XML_SIGNATURE: &str = "<?xml";

    let mut result = SignatureResult {
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_HIGH,
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
         * The current extractor (7z) cannot handle these signed DMGs anyway, and the beginning of the DMG is often compressed.
         * So while the DMG will not be matched, the compressed data will, and at least something gets extracted.
         *
         * Non-signed DMGs should be identified and extracted correctly.
         */

        // Make sure the length of image data and length of XML data are sane
        if (dmg_footer.data_length + dmg_footer.xml_length) <= offset {
            // Calculate the start and end offset of the XML tag, based on the XML data length provided in the DMG footer
            let start_xml_signature: usize = offset - dmg_footer.xml_length;
            let end_xml_signature: usize = start_xml_signature + XML_SIGNATURE.len();

            if let Some(xml_data) = file_data.get(start_xml_signature..end_xml_signature) {
                // Convert the XML tag to a string
                if let Ok(xml_signature) = String::from_utf8(xml_data.to_vec()) {
                    // XML tag should start with "<?xml"
                    if xml_signature == XML_SIGNATURE {
                        // Report the result
                        result.size =
                            dmg_footer.data_length + dmg_footer.xml_length + dmg_footer.footer_size;
                        result.offset = offset - (dmg_footer.data_length + dmg_footer.xml_length);
                        result.description =
                            format!("{}, total size: {} bytes", result.description, result.size);
                        return Ok(result);
                    }
                }
            }
        }
    }

    return Err(SignatureError);
}
