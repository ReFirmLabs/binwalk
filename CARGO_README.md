# binwalk

A Rust implementation of the Binwalk firmware analysis tool.

## System Requirements

Building requires the following system packages:

```
build-essential libfontconfig1-dev liblzma-dev
```

## Example

```
use binwalk::Binwalk;

// Create a new Binwalk instance
let binwalker = Binwalk::new();

// Read in the data to analyze
let file_data = std::fs::read("/tmp/firmware.bin").expect("Failed to read from file");

// Scan the file data and print the results
for result in binwalker.scan(&file_data) {
    println!("{:#?}", result);
}
```
