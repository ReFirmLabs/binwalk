use crate::structures::common::{parse, StructureError};

/// Struct to store LZFSE block info
#[derive(Debug, Default, Clone)]
pub struct LZFSEBlock {
    pub eof: bool,
    pub data_size: usize,
    pub header_size: usize,
}

/// Parse an LZFSE block header
pub fn parse_lzfse_block_header(lzfse_data: &[u8]) -> Result<LZFSEBlock, StructureError> {
    // LZFSE block types
    const ENDOFSTREAM: usize = 0x24787662;
    const UNCOMPRESSED: usize = 0x2d787662;
    const COMPRESSEDV1: usize = 0x31787662;
    const COMPRESSEDV2: usize = 0x32787662;
    const COMPRESSEDLZVN: usize = 0x6e787662;

    // Each block starts with a 4-byte magic identifier
    let block_type_structure = vec![("block_type", "u32")];

    // Parse the block header
    if let Ok(block_type_header) = parse(lzfse_data, &block_type_structure, "little") {
        let block_type = block_type_header["block_type"];

        // Block headers are different for different block types; process this block header accordingly
        if block_type == ENDOFSTREAM {
            return parse_endofstream_block_header(lzfse_data);
        } else if block_type == UNCOMPRESSED {
            return parse_uncompressed_block_header(lzfse_data);
        } else if block_type == COMPRESSEDV1 {
            return parse_compressedv1_block_header(lzfse_data);
        } else if block_type == COMPRESSEDV2 {
            return parse_compressedv2_block_header(lzfse_data);
        } else if block_type == COMPRESSEDLZVN {
            return parse_compressedlzvn_block_header(lzfse_data);
        }
    }

    Err(StructureError)
}

/// Parse an end-of-stream LZFSE block header
fn parse_endofstream_block_header(_lzfse_data: &[u8]) -> Result<LZFSEBlock, StructureError> {
    // This is easy; it's just the 4-byte magic bytes marking the end-of-stream
    Ok(LZFSEBlock {
        eof: true,
        data_size: 0,
        header_size: 4,
    })
}

/// Parse an uncompressed LZFSE block header
fn parse_uncompressed_block_header(lzfse_data: &[u8]) -> Result<LZFSEBlock, StructureError> {
    const HEADER_SIZE: usize = 8;

    let block_structure = vec![("magic", "u32"), ("n_raw_bytes", "u32")];

    if let Ok(header) = parse(lzfse_data, &block_structure, "little") {
        return Ok(LZFSEBlock {
            eof: false,
            data_size: header["n_raw_bytes"],
            header_size: HEADER_SIZE,
        });
    }

    Err(StructureError)
}

/// Parse a compressed (version 1) LZFSE block header
fn parse_compressedv1_block_header(lzfse_data: &[u8]) -> Result<LZFSEBlock, StructureError> {
    const HEADER_SIZE: usize = 770;

    let block_structure = vec![
        ("magic", "u32"),
        ("n_raw_bytes", "u32"),
        ("n_payload_bytes", "u32"),
        ("n_literals", "u32"),
        ("n_matches", "u32"),
        ("n_literal_payload_bytes", "u32"),
        ("n_lmd_payload_bytes", "u32"),
        ("literal_bits", "u32"),
        ("literal_state", "u64"),
        ("lmd_bits", "u32"),
        ("l_state", "u16"),
        ("m_state", "u16"),
        ("d_state", "u16"),
        // Frequency tables follow
    ];

    if let Ok(header) = parse(lzfse_data, &block_structure, "little") {
        return Ok(LZFSEBlock {
            eof: false,
            data_size: header["n_literal_payload_bytes"] + header["n_lmd_payload_bytes"],
            header_size: HEADER_SIZE,
        });
    }

    Err(StructureError)
}

/// Parse a compressed (version 2) LZFSE block header
fn parse_compressedv2_block_header(lzfse_data: &[u8]) -> Result<LZFSEBlock, StructureError> {
    const N_PAYLOAD_SHIFT: usize = 20;
    const LMD_PAYLOAD_SHIFT: usize = 40;
    const PAYLOAD_MASK: usize = 0b11111_11111_11111_11111;

    let block_structure = vec![
        ("magic", "u32"),
        ("uncompressed_size", "u32"),
        ("packed_field_1", "u64"),
        ("packed_field_2", "u64"),
        ("header_size", "u32"),
        ("state_fields", "u32"),
        // Variable length header field follows
    ];

    if let Ok(block_header) = parse(lzfse_data, &block_structure, "little") {
        let n_lmd_payload_bytes =
            (block_header["packed_field_2"] >> LMD_PAYLOAD_SHIFT) & PAYLOAD_MASK;
        let n_literal_payload_bytes =
            (block_header["packed_field_1"] >> N_PAYLOAD_SHIFT) & PAYLOAD_MASK;

        return Ok(LZFSEBlock {
            eof: false,
            data_size: n_lmd_payload_bytes + n_literal_payload_bytes,
            header_size: block_header["header_size"],
        });
    }

    Err(StructureError)
}

/// Parse a LZVN compressed LZFSE block header
fn parse_compressedlzvn_block_header(lzfse_data: &[u8]) -> Result<LZFSEBlock, StructureError> {
    const HEADER_SIZE: usize = 12;

    let block_structure = vec![
        ("magic", "u32"),
        ("n_raw_bytes", "u32"),
        ("n_payload_bytes", "u32"),
    ];

    if let Ok(header) = parse(lzfse_data, &block_structure, "little") {
        return Ok(LZFSEBlock {
            eof: false,
            data_size: header["n_payload_bytes"],
            header_size: HEADER_SIZE,
        });
    }

    Err(StructureError)
}
