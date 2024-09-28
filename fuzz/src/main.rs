use afl::fuzz;
use binwalk::Binwalk;

fn main() {
    // AFL makes this real simple...
    fuzz!(|data: &[u8]| {
        // Initialize binwalk, no extraction
        let binwalker = Binwalk::default();
        // Scan the data provided by AFL
        binwalker.scan(&data.to_vec());
    });
}
