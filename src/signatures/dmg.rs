use crate::signatures;
use crate::structures::dmg::parse_dmg_footer;

pub const DESCRIPTION: &str = "Apple Disk iMaGe";

pub fn dmg_magic() -> Vec<Vec<u8>> {
    // 4-byte magic, 4-byte version (v4), 4-byte structure size (0x0200)
    // This is actually the magic bytes of the DMG footer, there is no standard header format
    return vec![b"koly\x00\x00\x00\x04\x00\x00\x02\x00".to_vec()];
}

pub fn dmg_parser(
    file_data: &Vec<u8>,
    offset: usize,
) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {
    const XML_SIGNATURE: &str = "<?xml";

    let mut result = signatures::common::SignatureResult {
        description: DESCRIPTION.to_string(),
        confidence: signatures::common::CONFIDENCE_HIGHER_THAN_SNOOP_DOG,
        ..Default::default()
    };

    // Parse the DMG footer
    if let Ok(dmg_footer) = parse_dmg_footer(&file_data[offset..]) {
        /*
        * According to internet lore, DMG files have the following layout:
        *
        *      [ image data ]  [ xml data ]  [ footer ]
        *
        * We can only signature reliably on the footer, which does contain the offsets and sizes of the image data and xml data.
        * In theory, this would allow us to calculate the starting offset, and size, of the DMG image.
        *
        * In practice, there is, more often than not, additional data between the XML and the footer. This extra data appears to
        * be related to signing certificates and is variable in length, making the above theoretical calculations of the DMG offset
        * and size invalid.
        *
        * Until a better way can be found, this signature only works for DMG images whose starting file offset is 0. This is the most
        * common case, and means that the DMG size is just the offset of the footer (identified by the footer magic bytes), plus the
        * footer size, which is reliable.

        * This also means that DMGs embedded inside other files will not be identified. :(
        */
        if dmg_footer.data_offset == 0 {
            // Calculate the start and end offset of the XML tag, based on the XML offset provided in the DMG footer
            let start_xml_signature: usize = dmg_footer.xml_offset;
            let end_xml_signature: usize = start_xml_signature + XML_SIGNATURE.len();

            // Sanity check that this XML data falls inside the file data
            if start_xml_signature < file_data.len() && end_xml_signature < file_data.len() {
                // Convert the XML tag to a string
                if let Ok(xml_signature) =
                    String::from_utf8(file_data[start_xml_signature..end_xml_signature].to_vec())
                {
                    // XML tag should start with "<?xml"
                    if xml_signature == XML_SIGNATURE {
                        // Report the result
                        result.size = offset + dmg_footer.footer_size;
                        result.offset = dmg_footer.data_offset;
                        result.description =
                            format!("{}, total size: {} bytes", result.description, result.size);
                        return Ok(result);
                    }
                }
            }
        }
    }

    return Err(signatures::common::SignatureError);
}
