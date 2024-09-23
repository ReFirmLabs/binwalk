use crate::structures;

pub struct WebPHeader {
    pub size: usize,
    pub chunk_type: String,
}

pub fn parse_webp_header(webp_data: &[u8]) -> Result<WebPHeader, structures::common::StructureError> {
    const MAGIC1: usize = 0x46464952;
    const MAGIC2: usize = 0x50424557;

    const CHUNK_TYPE_START: usize = 12;
    const CHUNK_TYPE_END: usize = 15;

    const FILE_SIZE_OFFSET: usize = 8;

    let webp_structure = vec![
        ("magic1", "u32"),
        ("file_size", "u32"),
        ("magic2", "u32"),
        ("chunk_type", "u32"),
    ];

    let webp_struct_size: usize = structures::common::size(&webp_structure);

    // Sanity check the size of available data
    if webp_data.len() >= webp_struct_size {

        // Parse the webp header
        let webp_header = structures::common::parse(&webp_data, &webp_structure, "little");

        if webp_header["magic1"] == MAGIC1 && webp_header["magic2"] == MAGIC2 {
            if let Ok(type_string) = String::from_utf8(webp_data[CHUNK_TYPE_START..CHUNK_TYPE_END].to_vec()) {
                return Ok(WebPHeader {
                    size: webp_header["file_size"] + FILE_SIZE_OFFSET,
                    chunk_type: type_string.trim().to_string(),
                });
            }
        }
    }

    return Err(structures::common::StructureError);
}
