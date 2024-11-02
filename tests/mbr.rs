mod common;

#[test]
fn integration_test() {
    const SIGNATURE_TYPE: &str = "mbr";
    const INPUT_FILE_NAME: &str = "mbr.bin";
    common::integration_test(SIGNATURE_TYPE, INPUT_FILE_NAME);
}
