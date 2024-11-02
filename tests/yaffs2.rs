mod common;

#[test]
fn integration_test() {
    const SIGNATURE_TYPE: &str = "yaffs";
    const INPUT_FILE_NAME: &str = "yaffs2.bin";
    common::integration_test(SIGNATURE_TYPE, INPUT_FILE_NAME);
}
