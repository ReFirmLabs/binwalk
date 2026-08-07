use crate::structures::common::{self, StructureError};

/// Struct to store parsed LZ4L (UNISOC NV-storage wrapper) header data
#[derive(Debug, Default, Clone)]
pub struct Lz4lHeader {
    pub uncompressed_size: usize,
}

/// Sane maximum for uncompressed size (256 MiB)
const MAX_UNCOMP_SIZE: usize = 0x10000000;

/// Parse an LZ4L header
///
/// Layout (all little-endian):
///   [0..4)  magic              — ASCII "LZ4L"
///   [4..8)  uncompressed_size  — u32
///   [8..)   raw LZ4 block-format compressed data (no frame/block headers,
///           self-delimiting only by decompressing to uncompressed_size)
///
/// Confirmed via live extraction from a TUGE TM18NA (UNISOC V8850) LTE
/// module's `/factory` NV-calibration partition, pulled over AT+FSRDFILE:
/// this is a trivial 8-byte wrapper around the standard LZ4 *block* API
/// (not the LZ4 frame format the existing `lz4` module handles). The
/// header stores only the uncompressed size -- the smallest real sample
/// captured (11 bytes total: 8-byte header + 3-byte compressed payload)
/// proves there is no third field for a compressed-size, since there'd be
/// no room left for one.
pub fn parse_lz4l_header(data: &[u8]) -> Result<Lz4lHeader, StructureError> {
    let structure = vec![("magic", "u32"), ("uncompressed_size", "u32")];

    if let Ok(header) = common::parse(data, &structure, "little") {
        // "LZ4L" as little-endian u32
        const LZ4L_MAGIC: usize = 0x4C34_5A4C;
        if header["magic"] == LZ4L_MAGIC
            && header["uncompressed_size"] > 0
            && header["uncompressed_size"] < MAX_UNCOMP_SIZE
        {
            return Ok(Lz4lHeader {
                uncompressed_size: header["uncompressed_size"],
            });
        }
    }

    Err(StructureError)
}

/// Find the exact compressed length of a raw LZ4 block given the expected
/// uncompressed size.
///
/// The LZ4L wrapper stores only the uncompressed size, never the compressed
/// size, and the raw LZ4 block format itself has no end-of-block marker to
/// self-delimit it (unlike the LZ4 *frame* format, which chops data into
/// explicitly-sized blocks). The underlying C decompressor (LZ4_decompress_safe)
/// requires the exact compressed length as an input and has no API to report
/// how many bytes it actually consumed if given more -- confirmed live: the
/// same real compressed data that decodes cleanly when given its exact
/// length fails outright ("Input invalid or too long?") when given the same
/// data plus even a few bytes of trailing garbage.
///
/// So the true compressed length has to be found by trying candidate
/// lengths and checking which one decompresses to exactly
/// `uncompressed_size` bytes. `LZ4_compressBound(uncompressed_size)` is a
/// hard mathematical ceiling on how large a valid encoding of that many
/// bytes could ever be, so the search only needs to check up to that bound
/// (or less, if less data is actually available) -- not the entire rest of
/// a large surrounding file.
pub fn find_lz4l_compressed_length(available: &[u8], uncompressed_size: usize) -> Option<usize> {
    let upper_bound = match lz4::block::compress_bound(uncompressed_size) {
        Ok(bound) => std::cmp::min(bound, available.len()),
        Err(_) => available.len(),
    };

    for candidate_len in 1..=upper_bound {
        if let Ok(decompressed) =
            lz4::block::decompress(&available[..candidate_len], Some(uncompressed_size as i32))
        {
            if decompressed.len() == uncompressed_size {
                return Some(candidate_len);
            }
        }
    }

    None
}
