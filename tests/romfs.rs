mod common;

#[test]
fn integration_test() {
    const SIGNATURE_TYPE: &str = "romfs";
    const INPUT_FILE_NAME: &str = "romfs.bin";
    common::integration_test(SIGNATURE_TYPE, INPUT_FILE_NAME);
}
