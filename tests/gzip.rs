mod common;

#[test]
fn gzip_integration() {
    const SIGNATURE_TYPE: &str = "gzip";
    const INPUT_FILE_NAME: &str = "gzip.bin";
    let _ = common::integration_test(SIGNATURE_TYPE, INPUT_FILE_NAME);
}
