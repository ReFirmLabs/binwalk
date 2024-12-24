mod common;

#[test]
fn integration_test() {
    const SIGNATURE_TYPE: &str = "squashfs";
    const INPUT_FILE_NAME: &str = "squashfs_v2.bin";
    common::integration_test(SIGNATURE_TYPE, INPUT_FILE_NAME);
}
