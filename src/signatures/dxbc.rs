use crate::signatures::common::{
    SignatureError, SignatureResult, CONFIDENCE_HIGH, CONFIDENCE_MEDIUM,
};
use crate::structures::dxbc::parse_dxbc_header;

/// Human readable description
pub const DESCRIPTION: &str = "DirectX shader bytecode";

/// DXBC file magic bytes
pub fn dxbc_magic() -> Vec<Vec<u8>> {
    vec![b"DXBC".to_vec()]
}

/// Validates the DXBC header
pub fn dxbc_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    const CHUNK_SM4: [u8; 4] = *b"SHDR";
    const CHUNK_SM5: [u8; 4] = *b"SHEX";

    // Successful return value
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    if let Ok(header) = parse_dxbc_header(&file_data[offset..]) {
        result.confidence = CONFIDENCE_HIGH;
        result.size = header.size;

        let shader_model = if header.chunk_ids.contains(&CHUNK_SM4) {
            "Shader Model 4"
        } else if header.chunk_ids.contains(&CHUNK_SM5) {
            "Shader Model 5"
        } else {
            "Unknown Shader Model"
        };

        result.description = format!("{}, {}", result.description, shader_model);

        return Ok(result);
    }

    Err(SignatureError)
}
