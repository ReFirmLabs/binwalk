mod common;

#[test]
fn integration_test() {
    const SIGNATURE_TYPE: &str = "gzip";
    const INPUT_FILE_NAME: &str = "gzip.bin";
    common::integration_test(SIGNATURE_TYPE, INPUT_FILE_NAME);
}
