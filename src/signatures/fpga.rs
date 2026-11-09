use crate::signatures::common::{
    CONFIDENCE_HIGH, CONFIDENCE_LOW, CONFIDENCE_MEDIUM, SignatureError, SignatureResult,
};

/// Human readable descriptions
pub const XILINX_DESCRIPTION: &str = "Xilinx FPGA bitstream";
pub const ICE40_DESCRIPTION: &str = "Lattice iCE40 FPGA bitstream";

/// Xilinx .bit header field 1 (length 9 + fixed magic), then field 2 length (1) and key 'a'
/// (UG470 / prjxray bitstream documentation), and the raw configuration bus-width sync pattern
/// 0x000000BB 0x11220044 that precedes the 0xAA995566 sync word in .bit and .bin files.
pub fn xilinx_magic() -> Vec<Vec<u8>> {
    vec![
        b"\x00\x09\x0f\xf0\x0f\xf0\x0f\xf0\x0f\xf0\x00\x00\x01\x61".to_vec(),
        b"\x00\x00\x00\xbb\x11\x22\x00\x44".to_vec(),
    ]
}

/// iCE40 preamble (icestorm documentation: "7EAA997E")
pub fn ice40_magic() -> Vec<Vec<u8>> {
    vec![b"\x7e\xaa\x99\x7e".to_vec()]
}

const XILINX_SYNC: [u8; 4] = [0xaa, 0x99, 0x55, 0x66];
const BIT_HEADER_LEN: usize = 13;

/// Read a big-endian u16-length-prefixed field at `p`; returns (value, next offset)
fn bit_field(data: &[u8], p: usize) -> Option<(&[u8], usize)> {
    let len = u16::from_be_bytes([*data.get(p)?, *data.get(p + 1)?]) as usize;
    let start = p + 2;
    let value = data.get(start..start + len)?;
    Some((value, start + len))
}

fn field_text(value: &[u8]) -> String {
    String::from_utf8_lossy(value)
        .trim_end_matches('\0')
        .chars()
        .filter(|c| !c.is_control())
        .collect()
}

/// Validates a Xilinx .bit file header, or a raw bitstream bus-width/sync sequence
pub fn xilinx_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    let mut result = SignatureResult {
        offset,
        description: XILINX_DESCRIPTION.to_string(),
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    // .bit header: field 'a' (design), 'b' (part), 'c' (date), 'd' (time), 'e' (u32 data length)
    if file_data.get(offset + BIT_HEADER_LEN) == Some(&b'a') {
        let mut p = offset + BIT_HEADER_LEN + 1;
        let mut text: Vec<String> = Vec::new();
        for key in [b'b', b'c', b'd'] {
            let (value, next) = bit_field(file_data, p).ok_or(SignatureError)?;
            text.push(field_text(value));
            if file_data.get(next) != Some(&key) {
                return Err(SignatureError);
            }
            p = next + 1;
        }
        let (value, next) = bit_field(file_data, p).ok_or(SignatureError)?;
        text.push(field_text(value));
        if file_data.get(next) != Some(&b'e') {
            return Err(SignatureError);
        }
        let len_bytes = file_data.get(next + 1..next + 5).ok_or(SignatureError)?;
        let data_len =
            u32::from_be_bytes(len_bytes.try_into().map_err(|_| SignatureError)?) as usize;
        let data_start = next + 5;
        let window = file_data
            .get(data_start..data_start + data_len.min(256))
            .ok_or(SignatureError)?;
        if !window.windows(4).any(|w| w == XILINX_SYNC) {
            return Err(SignatureError);
        }
        result.size = data_start + data_len - offset;
        result.confidence = CONFIDENCE_HIGH;
        result.description = format!(
            "{}, design: {}, part: {}, date: {} {}, total size: {} bytes",
            XILINX_DESCRIPTION, text[0], text[1], text[2], text[3], result.size
        );
        return Ok(result);
    }

    // Raw bitstream: bus-width pattern, then only 0xFF padding before the sync word
    let after = offset + 8;
    let window = file_data.get(after..after + 64).ok_or(SignatureError)?;
    if let Some(pos) = window.windows(4).position(|w| w == XILINX_SYNC)
        && window[..pos].iter().all(|b| *b == 0xff)
    {
        result.description = format!("{XILINX_DESCRIPTION}, raw (no .bit header)");
        return Ok(result);
    }
    Err(SignatureError)
}

/// Walks the iCE40 command stream (opcode in the high nibble, payload length in the low nibble)
/// until the wakeup command; CRAM/BRAM data blocks are width * height / 8 bytes plus 2.
pub fn ice40_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    let mut p = offset + 4;
    let (mut width, mut height) = (0usize, 0usize);
    let mut commands = 0;

    while let Some(&cmd) = file_data.get(p) {
        let (op, n) = (cmd >> 4, (cmd & 0x0f) as usize);
        let payload = file_data.get(p + 1..p + 1 + n).ok_or(SignatureError)?;
        let value = payload
            .iter()
            .fold(0usize, |acc, b| (acc << 8) | *b as usize);
        p += 1 + n;
        commands += 1;
        match op {
            6 => width = value + 1,
            7 => height = value,
            1 | 2 | 5 | 8 | 9 => {}
            0 => match value {
                1 | 3 => p += width * height / 8 + 2, // CRAM / BRAM data block
                5 => {}                               // CRC reset
                6 => {
                    // wakeup: done; icepack pads one trailing zero byte
                    if file_data.get(p) == Some(&0) {
                        p += 1;
                    }
                    let size = p - offset;
                    if size > file_data.len() - offset || commands < 4 {
                        return Err(SignatureError);
                    }
                    return Ok(SignatureResult {
                        offset,
                        size,
                        confidence: CONFIDENCE_HIGH,
                        description: format!("{ICE40_DESCRIPTION}, total size: {size} bytes"),
                        ..Default::default()
                    });
                }
                _ => return Err(SignatureError),
            },
            _ => return Err(SignatureError),
        }
    }

    // Truncated stream: report only if it parsed a plausible header
    if commands >= 4 {
        return Ok(SignatureResult {
            offset,
            confidence: CONFIDENCE_LOW,
            description: format!("{ICE40_DESCRIPTION}, truncated"),
            ..Default::default()
        });
    }
    Err(SignatureError)
}
