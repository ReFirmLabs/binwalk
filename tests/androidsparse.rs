//! Regression tests for the Android sparse extractor.
//!
//! Covers three DoS bugs reported in `BUG_REPORT.md` against v3.1.1:
//!
//!   1. Infinite loop when a FILL chunk has total_size == 12 (no fill payload)
//!   2. Disk / memory exhaustion via uncapped block_count and block_size
//!   3. Integer underflow when chunk total_size < chunk header size (12)

use binwalk::Binwalk;
use binwalk::extractors::androidsparse::extract_android_sparse;
use binwalk::structures::androidsparse::parse_android_sparse_chunk_header;

const SPARSE_MAGIC: u32 = 0xED26FF3A;
const FILE_HEADER_SIZE: u16 = 28;
const CHUNK_HEADER_SIZE: u16 = 12;
const CHUNK_TYPE_RAW: u16 = 0xCAC1;
const CHUNK_TYPE_FILL: u16 = 0xCAC2;
const CHUNK_TYPE_DONT_CARE: u16 = 0xCAC3;

/// Build an Android sparse file header.
fn sparse_header(block_size: u32, block_count: u32, total_chunks: u32) -> Vec<u8> {
    let mut h = Vec::new();
    h.extend_from_slice(&SPARSE_MAGIC.to_le_bytes());
    h.extend_from_slice(&1u16.to_le_bytes()); // major_version
    h.extend_from_slice(&0u16.to_le_bytes()); // minor_version
    h.extend_from_slice(&FILE_HEADER_SIZE.to_le_bytes());
    h.extend_from_slice(&CHUNK_HEADER_SIZE.to_le_bytes());
    h.extend_from_slice(&block_size.to_le_bytes());
    h.extend_from_slice(&block_count.to_le_bytes());
    h.extend_from_slice(&total_chunks.to_le_bytes());
    h.extend_from_slice(&0u32.to_le_bytes()); // checksum (unchecked)
    h
}

/// Build an Android sparse chunk header.
fn chunk_header(chunk_type: u16, output_block_count: u32, total_size: u32) -> Vec<u8> {
    let mut c = Vec::new();
    c.extend_from_slice(&chunk_type.to_le_bytes());
    c.extend_from_slice(&0u16.to_le_bytes()); // reserved
    c.extend_from_slice(&output_block_count.to_le_bytes());
    c.extend_from_slice(&total_size.to_le_bytes());
    c
}

/// Per-test output dir under the OS temp dir so tests don't collide with each
/// other or pollute the repo.
fn test_output_dir(name: &str) -> String {
    let dir = std::env::temp_dir().join(format!("binwalk_androidsparse_test_{name}"));
    let _ = std::fs::remove_dir_all(&dir);
    std::fs::create_dir_all(&dir).expect("failed to create test output dir");
    dir.display().to_string()
}

// ---------------------------------------------------------------------------
// Bug 3 — integer underflow when chunk total_size < header_size
// ---------------------------------------------------------------------------

/// A chunk header reporting total_size < CHUNK_HEADER_SIZE used to underflow
/// `total_size - header_size` and panic in debug builds (and wrap to a huge
/// usize in release). The parser must now reject it cleanly.
#[test]
fn chunk_header_total_size_below_header_size_is_rejected() {
    for bad_total_size in [0u32, 1, 11] {
        let bytes = chunk_header(CHUNK_TYPE_DONT_CARE, 1, bad_total_size);
        let res = parse_android_sparse_chunk_header(&bytes);
        assert!(
            res.is_err(),
            "expected parser to reject total_size={bad_total_size}, got Ok"
        );
    }
}

/// End-to-end: a sparse image whose first chunk has total_size=0 must not
/// panic during a dry-run scan (the signature parser calls the extractor in
/// dry-run mode, so an underflow here would crash the whole scan).
#[test]
fn underflow_chunk_does_not_panic_during_scan() {
    let mut img = sparse_header(4, 1, 1);
    img.extend(chunk_header(CHUNK_TYPE_DONT_CARE, 1, 0));

    // Dry-run via the extractor directly (matches what the signature parser does).
    let result = extract_android_sparse(&img, 0, None);
    assert!(!result.success, "malformed chunk should not extract");

    // And via the full scan pipeline, for good measure.
    let binwalker = Binwalk::new();
    let _ = binwalker.scan(&img); // must not panic
}

// ---------------------------------------------------------------------------
// Bug 1 — infinite loop when FILL chunk carries no fill payload
// ---------------------------------------------------------------------------

/// A FILL chunk per the spec carries a 4-byte fill value. A chunk advertising
/// total_size=12 (i.e., data_size=0) used to make the extractor spin forever
/// in `while i < block_size { fill_block.extend(&[]); i += 0; }`. The parser
/// must now reject this shape outright.
#[test]
fn fill_chunk_with_no_payload_is_rejected_by_parser() {
    let bytes = chunk_header(CHUNK_TYPE_FILL, 1, 12);
    assert!(parse_android_sparse_chunk_header(&bytes).is_err());
}

/// End-to-end: a sparse image whose FILL chunk has total_size=12 must not
/// hang. Cargo's test runner has no per-test timeout, so if this test ever
/// hangs CI will eventually kill it and the regression will be obvious.
#[test]
fn fill_chunk_with_no_payload_does_not_hang_extraction() {
    let mut img = sparse_header(4096, 1, 1);
    img.extend(chunk_header(CHUNK_TYPE_FILL, 1, 12)); // total_size==12 -> no payload

    let outdir = test_output_dir("fill_no_payload");
    let result = extract_android_sparse(&img, 0, Some(&outdir));

    assert!(
        !result.success,
        "extractor should refuse a FILL chunk with no fill data, not loop on it"
    );
    let _ = std::fs::remove_dir_all(&outdir);
}

/// Defense in depth: a non-empty FILL payload that happens to also have
/// data_size != 4 is rejected. (Helps prevent future regressions if someone
/// loosens the parser.)
#[test]
fn fill_chunk_with_wrong_payload_size_is_rejected() {
    // total_size = 12 + 8 = 20 (8 bytes of fill, spec says 4)
    let bytes = chunk_header(CHUNK_TYPE_FILL, 1, 20);
    assert!(parse_android_sparse_chunk_header(&bytes).is_err());
}

// ---------------------------------------------------------------------------
// Bug 2 — disk / memory exhaustion via uncapped block_count / block_size
// ---------------------------------------------------------------------------

/// A sparse header whose block_count * block_size would overflow usize must be
/// rejected before extraction allocates anything.
#[test]
fn header_with_overflowing_total_size_is_rejected() {
    // u32::MAX & ~3 to satisfy block_size % 4 == 0
    let huge = u32::MAX & !3u32;
    let mut img = sparse_header(huge, huge, 1);
    img.extend(chunk_header(CHUNK_TYPE_DONT_CARE, 1, 12));

    let outdir = test_output_dir("overflow_total_size");
    let result = extract_android_sparse(&img, 0, Some(&outdir));
    assert!(
        !result.success,
        "sparse header with overflowing block_count*block_size must be rejected"
    );

    // And nothing should have been written.
    let written: u64 = walk_size(&outdir);
    assert_eq!(written, 0, "extractor wrote {written} bytes for a rejected image");

    let _ = std::fs::remove_dir_all(&outdir);
}

/// A sparse header whose declared total output size is huge but doesn't
/// overflow (e.g., 256 TB) must still be rejected.
#[test]
fn header_with_oversized_but_nonoverflowing_total_is_rejected() {
    // 256 TB = 2^48; block_size = 64 KiB, block_count = 2^32
    let block_size: u32 = 64 * 1024;
    let block_count: u32 = u32::MAX;
    let mut img = sparse_header(block_size, block_count, 1);
    img.extend(chunk_header(CHUNK_TYPE_DONT_CARE, 1, 12));

    let outdir = test_output_dir("oversized_total");
    let result = extract_android_sparse(&img, 0, Some(&outdir));
    assert!(!result.success, "256TB-class sparse image must be rejected");

    let written: u64 = walk_size(&outdir);
    assert_eq!(written, 0);

    let _ = std::fs::remove_dir_all(&outdir);
}

/// Even if the *header* declares a sane total, an individual chunk must not be
/// able to claim more blocks than the entire image. This prevents a single
/// DONT_CARE/FILL chunk from driving giant writes.
#[test]
fn chunk_claiming_more_blocks_than_header_is_rejected() {
    // Header: 1 block total. Chunk: claims a billion blocks.
    let mut img = sparse_header(4096, 1, 1);
    img.extend(chunk_header(CHUNK_TYPE_DONT_CARE, 1_000_000_000, 12));

    let outdir = test_output_dir("chunk_exceeds_header");
    let result = extract_android_sparse(&img, 0, Some(&outdir));
    assert!(
        !result.success,
        "chunk block_count > header block_count must be rejected"
    );

    let written: u64 = walk_size(&outdir);
    assert_eq!(written, 0);

    let _ = std::fs::remove_dir_all(&outdir);
}

/// RAW chunks must carry exactly block_count * block_size bytes of payload.
/// A header lying about that would let an attacker drive huge reads on tiny
/// input files.
#[test]
fn raw_chunk_with_mismatched_payload_size_is_rejected() {
    // Header: 16 blocks of 4 bytes. Chunk: claims 16 blocks but carries only 4 bytes.
    let mut img = sparse_header(4, 16, 1);
    img.extend(chunk_header(CHUNK_TYPE_RAW, 16, 12 + 4));
    img.extend_from_slice(&[0u8; 4]);

    let outdir = test_output_dir("raw_size_mismatch");
    let result = extract_android_sparse(&img, 0, Some(&outdir));
    assert!(
        !result.success,
        "RAW chunk with payload != block_count*block_size must be rejected"
    );
    let _ = std::fs::remove_dir_all(&outdir);
}

// ---------------------------------------------------------------------------
// Positive control — minimal well-formed sparse image still extracts cleanly
// ---------------------------------------------------------------------------

/// Sanity check: the fixes don't break extraction of a legitimate (if tiny)
/// sparse image. One DONT_CARE chunk produces block_size bytes of zeros.
#[test]
fn valid_minimal_sparse_image_extracts_successfully() {
    let block_size: u32 = 4;
    let total_blocks: u32 = 1;
    let mut img = sparse_header(block_size, total_blocks, 1);
    img.extend(chunk_header(CHUNK_TYPE_DONT_CARE, 1, 12));

    let outdir = test_output_dir("valid_minimal");
    let result = extract_android_sparse(&img, 0, Some(&outdir));
    assert!(result.success, "minimal valid sparse image failed to extract");

    let unsparsed = std::path::Path::new(&outdir).join("unsparsed.img");
    let bytes = std::fs::read(&unsparsed).expect("expected output file");
    assert_eq!(bytes, vec![0u8; block_size as usize]);

    let _ = std::fs::remove_dir_all(&outdir);
}

/// Sum the size of every regular file beneath `dir`.
fn walk_size(dir: &str) -> u64 {
    let mut total: u64 = 0;
    if let Ok(entries) = std::fs::read_dir(dir) {
        for entry in entries.flatten() {
            if let Ok(meta) = entry.metadata() {
                if meta.is_file() {
                    total += meta.len();
                } else if meta.is_dir() {
                    total += walk_size(&entry.path().display().to_string());
                }
            }
        }
    }
    total
}
