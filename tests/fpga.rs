mod common;

#[test]
fn ice40_integration_test() {
    // A real icepack bitstream (UP5K) embedded at offset 0x100; the preamble follows a 4-byte comment
    let expected_signature_offsets: Vec<usize> = vec![0x104];
    let expected_extraction_offsets: Vec<usize> = vec![];
    let results = common::run_binwalk("ice40_bitstream", "ice40_bitstream.bin");
    common::assert_results_ok(
        results,
        expected_signature_offsets,
        expected_extraction_offsets,
    );
}

#[test]
fn xilinx_integration_test() {
    // Synthetic .bit file (header fields a-e, dummy words, bus-width pattern, sync word) at 0x80
    let expected_signature_offsets: Vec<usize> = vec![0x80];
    let expected_extraction_offsets: Vec<usize> = vec![];
    let results = common::run_binwalk("xilinx_bitstream", "xilinx_bitstream.bin");
    common::assert_results_ok(
        results,
        expected_signature_offsets,
        expected_extraction_offsets,
    );
}
