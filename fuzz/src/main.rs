use afl::fuzz;
use binwalk::binwalk;

fn main() {
    // AFL makes this real simple...
    fuzz!(|data: &[u8]| {
        // Initialize binwalk, no extraction
        if let Ok(bwconfig) = binwalk::init(None, None, None, None) {
            // Scan the data provided by AFL
            binwalk::scan(&bwconfig, &data.to_vec());
        }
    });
}
