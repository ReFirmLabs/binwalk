use crate::structures::common::StructureError;
use aho_corasick::AhoCorasick;

const SVG_OPEN_TAG: &[u8] = b"<svg ";
const SVG_CLOSE_TAG: &[u8] = b"</svg>";
const SVG_HEAD_MAGIC: &str = "xmlns=\"http://www.w3.org/2000/svg\"";

/// Stores info about an SVG image
#[derive(Debug, Default, Clone)]
pub struct SVGImage {
    pub total_size: usize,
}

/// Parse an SVG image to determine its total size
pub fn parse_svg_image(svg_data: &[u8]) -> Result<SVGImage, StructureError> {
    let mut head_tag_count: usize = 0;
    let mut unclosed_svg_tags: usize = 0;

    let svg_tags = vec![SVG_OPEN_TAG, SVG_CLOSE_TAG];

    let grep = AhoCorasick::new(svg_tags).unwrap();

    // Need to search through the data to find all <svg ...> and </svg> tags.
    // There may be multiple of these tags in any given SVG image.
    for tag_match in grep.find_overlapping_iter(svg_data) {
        let tag_start: usize = tag_match.start();

        match parse_svg_tag(&svg_data[tag_start..]) {
            Err(_) => {
                break;
            }
            Ok(svg_tag) => {
                if svg_tag.is_head {
                    head_tag_count += 1;
                }

                if svg_tag.is_open {
                    unclosed_svg_tags += 1;
                }

                if svg_tag.is_close {
                    unclosed_svg_tags -= 1;
                }

                // There should be only one head tag
                if head_tag_count > 1 {
                    break;
                }

                // If one head tag was found and all svg tags are closed, that's EOF
                if head_tag_count == 1 && unclosed_svg_tags == 0 {
                    return Ok(SVGImage {
                        total_size: tag_start + SVG_CLOSE_TAG.len(),
                    });
                }
            }
        }
    }

    Err(StructureError)
}

/// Stores info about a parsed SVG tag
#[derive(Debug, Default, Clone)]
struct SVGTag {
    pub is_head: bool,
    pub is_open: bool,
    pub is_close: bool,
}

/// Parse an individual SVG tag
fn parse_svg_tag(tag_data: &[u8]) -> Result<SVGTag, StructureError> {
    const END_TAG: u8 = 0x3E;

    let mut result = SVGTag {
        ..Default::default()
    };

    let svg_open_tag = String::from_utf8(SVG_OPEN_TAG.to_vec()).unwrap();
    let svg_close_tag = String::from_utf8(SVG_CLOSE_TAG.to_vec()).unwrap();
    let svg_head_string = SVG_HEAD_MAGIC.to_string();

    // Tags are expected to start with '<svg' or </svg>', and end with '>'
    for i in 0..tag_data.len() {
        if tag_data[i] == END_TAG {
            if let Some(tag_bytes) = tag_data.get(0..i + 1) {
                if let Ok(tag_string) = String::from_utf8(tag_bytes.to_vec()) {
                    result.is_open = tag_string.starts_with(&svg_open_tag);
                    result.is_close = tag_string.starts_with(&svg_close_tag);
                    result.is_head = tag_string.contains(&svg_head_string);
                    return Ok(result);
                }
            }
        }
    }

    Err(StructureError)
}
