mod common;

#[test]
fn integration_test() {
    const SIGNATURE_TYPE: &str = "bzip2";
    const INPUT_FILE_NAME: &str = "bzip2.bin";
    common::integration_test(SIGNATURE_TYPE, INPUT_FILE_NAME);
}
