use std::collections::HashMap;

use crate::common::get_cstring;
use crate::structures::common::{self, StructureError};

/// Struct to store Matter OTA header info
#[derive(Debug, Default, Clone)]
pub struct MatterOTAHeader {
    pub total_size: usize,
    pub header_size: usize,
    pub vendor_id: usize,
    pub product_id: usize,
    pub version: String,
    pub payload_size: usize,
    pub image_digest_type: usize,
    pub image_digest: String,
}

#[derive(Debug)]
enum Value {
    Struct,
    EndOfContainer,
    Unsigned(usize),
    String(String),
    OctetString(Vec<u8>),
}

#[derive(Debug)]
struct Element {
    tag: Option<usize>,
    value: Value,
}

/// Parse a Matter OTA firmware header
pub fn parse_matter_ota_header(ota_data: &[u8]) -> Result<MatterOTAHeader, StructureError> {
    let ota_structure = vec![
        ("magic", "u32"),
        ("total_size", "u64"),
        ("header_size", "u32"),
    ];

    if let Ok(ota_header) = common::parse(ota_data, &ota_structure, "little") {
        let total_size: usize = ota_header["total_size"];
        let header_size: usize = ota_header["header_size"];

        // Header starts after the magic, total size and header size fields
        let header_start = common::size(&ota_structure);
        let header_end = header_start + header_size;
        let header_data = &ota_data[header_start..header_end];

        let header = parse_tlv_header(header_data)?;

        let mut result = MatterOTAHeader {
            total_size,
            header_size,
            ..Default::default()
        };

        for (key, value) in header.into_iter() {
            match (key.as_ref(), value) {
                ("VendorID", Value::Unsigned(vendor_id)) => result.vendor_id = vendor_id,
                ("ProductID", Value::Unsigned(product_id)) => result.product_id = product_id,
                ("SoftwareVersionString", Value::String(version)) => result.version = version,
                ("PayloadSize", Value::Unsigned(payload_size)) => {
                    result.payload_size = payload_size
                }
                ("ImageDigestType", Value::Unsigned(image_digest_type)) => {
                    result.image_digest_type = image_digest_type
                }
                ("ImageDigest", Value::OctetString(image_digest)) => {
                    let mut digest_string = String::new();
                    for b in image_digest {
                        digest_string.push_str(&format!("{:02x}", b));
                    }
                    result.image_digest = digest_string;
                }
                // Ignore other fields
                _ => {}
            }
        }

        // Sanity check
        if (result.payload_size + header_start + header_size) == total_size {
            return Ok(result);
        }
    }
    Err(StructureError)
}

/// Parse tlv element, return result and new offset
fn parse_tlv_element(data: &[u8]) -> Result<(Element, usize), StructureError> {
    let control_octet = data.first().ok_or(StructureError)?;

    let element_type = control_octet & 0x1f;
    let tag_control = control_octet >> 5;

    // Lower 2 bits of the control octet determine the field width of integer types
    // or the width of the length field for string types
    let field_width_type = match element_type & 0x3 {
        0 => "u8",
        1 => "u16",
        2 => "u32",
        3 => "u64",
        _ => return Err(StructureError),
    };

    // Parse numerical tag. Only supports anonymous fields and fields with a one byte tag
    let (tag, field_offset) = match tag_control {
        0 => (None, 1), // Anonymous field
        1 => (Some(*data.get(1).ok_or(StructureError)? as usize), 2),
        _ => return Err(StructureError),
    };

    let field_data = &data[field_offset..];

    match element_type {
        0b1_0101 => Ok((
            // Struct container
            Element {
                tag,
                value: Value::Struct,
            },
            field_offset,
        )),
        0b1_1000 => Ok((
            // End of container
            Element {
                tag,
                value: Value::EndOfContainer,
            },
            field_offset,
        )),
        0b0_0100..=0b0_0111 => {
            // Unsigned integer
            let structure = &vec![("field", field_width_type)];
            let result = common::parse(field_data, structure, "little")?;
            Ok((
                Element {
                    tag,
                    value: Value::Unsigned(result["field"]),
                },
                field_offset + common::size(structure),
            ))
        }
        0b0_1100..=0b0_1111 => {
            // UTF-8 String
            let structure = &vec![("string_length", field_width_type)];
            let result = common::parse(field_data, structure, "little")?;
            let string_length = result["string_length"] as usize;
            let string_data = &field_data[common::size(structure)..];
            let string = get_cstring(&string_data[..string_length]);
            Ok((
                Element {
                    tag,
                    value: Value::String(string),
                },
                field_offset + common::size(structure) + string_length,
            ))
        }
        0b1_0000..=0b1_0011 => {
            // Octet string
            let structure = &vec![("octet_string_length", field_width_type)];
            let result = common::parse(field_data, structure, "little")?;
            let octet_string_length = result["octet_string_length"] as usize;
            let octet_string_data = &field_data[common::size(structure)..];
            Ok((
                Element {
                    tag,
                    value: Value::OctetString(octet_string_data[..octet_string_length].to_vec()),
                },
                field_offset + common::size(structure) + octet_string_length,
            ))
        }
        _ => Err(StructureError), // Other types are not implemented, but not necessary for header parsing
    }
}

fn parse_tlv_header(data: &[u8]) -> Result<HashMap<String, Value>, StructureError> {
    // Field names for the Matter OTA header indexed by the tag number
    let fields = [
        "VendorID",
        "ProductID",
        "SoftwareVersion",
        "SoftwareVersionString",
        "PayloadSize",
        "MinApplicableSoftwareVersion",
        "MaxApplicableSoftwareVersion",
        "ReleaseNotesURL",
        "ImageDigestType",
        "ImageDigest",
    ];
    let mut offset = 0;
    let mut header = HashMap::new();
    while offset < data.len() {
        let (element, new_offset) = parse_tlv_element(&data[offset..])?;
        offset += new_offset;
        if let Some(tag) = element.tag {
            let field_name = *fields.get(tag).ok_or(StructureError)?;
            header.insert(field_name.to_string(), element.value);
        }
    }
    Ok(header)
}
