# Creating Signatures

There are three steps to defining a new signature:

1. Create a new `.rs` file in the `signatures` directory and write a signature parser
2. Import the new `.rs` file by adding it to the `signatures.rs` file
3. Define the new signature with a `signatures::common::Signature` structure entry in `magic.rs`

## Writing a Signature Parser

Signature parsers are at the heart of each defined signature.

Signature parsers must conform to the `signatures::common::SignatureParser` type definition.
They are provided two arguments: the raw file data, and an offset into the file data to begin parsing.

Signature parsers must parse and validate the expected signature data, and return either a `signatures::common::SignatureResult`
structure on success, or a `signatures::common::SignatureError` on failure. The signature parser should define a confidence level,
and if possible, the total size of the signature data, in the `SignatureResult` structure.

By convention, the signature description string and the magic bytes associated with the signature should be defined in the same file as the signature parser.

## Example

We want to identify a new, contrived, file type, the `FooBar file system`, which starts with the following header structure:

```
struct {
    u64 magic;      // 'FooBar\x00\x00'
    u8 flags;       // File system flags; only two flags are defined: 1 and 2. Any other flag values are invalid.
    u32 reserved;   // Reserved field, must be 0
    u32 size;       // The total size of the file system image, including the header
}
```

All fields for this made-up file system are stored in big-endian format.

*NOTE:* It is best practice to place the code repsonsible for structure parsing in the `structures` directory, and import that specific
structure parser into the signature code. In this example, for simplicity, we will parse the data structure directly in the signature parser.

See [structures/README.md](../structures/README.md) for more details on structure parsing.

#### Step 1

Create a new file, `signatures/foobar.rs` with the following contents:

```rust
// Provides some convenience functions for parsing basic data structures
use crate::structures;

// To access the signatures::common structure definitions
use crate::signatures;

/*
 * A short human-readable string defining what file type this signature is for.
 * This is the description that we will use later on when defining the signatures::common::Signature
 * structure in magic.rs, and hence will be the text displayed for this signature
 * whenever binwalk --list is run.
 */
pub const DESCRIPTION: &str = "FooBar filesystem";

/*
 * This function returns a list of magic signatures associated with the FooBar file system.
 * Some file types may have multiple magic signatures due to big/little endianness, or simply
 * because they have no official "magic bytes" (ex: LZMA). In this case, there is only one set
 * of magic bytes to search for.
 *
 * This function will be invoked later on when defining the signatures::common::Signature structure
 * in magic.rs.
 */
pub fn foobar_magic() -> Vec<Vec<u8>> {
    return vec![
        b"FooBar\x00\x00".to_vec(),
    ];
}

/*
 * This function is responsible for parsing and validating the FooBar file system data whenever the "magic bytes"
 * are found inside a file. It is provided access to the entire file data, and an offset into the file data where
 * the magic bytes were found. On success, it will return a signatures::common::SignatureResult structure.
 *
 * This function will be referenced later on when defining the signatures::common::Signature structure in magic.rs.
 */
pub fn foobar_parser(file_data: &Vec<u8>, offset: usize) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {
    // Define the structure of the FooBar header
    let foobar_header_structure = vec![
        ("magic", "u64"),
        ("flags", "u8"),
        ("reserved", "u32"),
        ("image_size", "u32"),
    ];

    // We know the flags field should only be one of these two values; we'll verify that below
    let allowed_flags: Vec<usize> = vec![1, 2];

    /*
     * This will be returned if the format of the suspected FooBar file system looks correct.
     * We will update it later with more information, but for now just define what is known
     * (the offset where the FooBar file system starts, the human-readable description, and
     * a confidence level), and leave the remaining fields at their defaults.
     *
     * Note that confidence level is chosen somewhat arbitrarily, and should be one of:
     *
     *   - CONFIDENCE_LOW (the default)
     *   - CONFIDENCE_MEDIUM
     *   - CONFIDENCE_HIGH
     *
     * In this case the magic byte field is 8 bytes long, which is relatively strong (most
     * file formats use 4 bytes for their magic field), and we will be performing some additional
     * sanity checks on the header fields, so the confidence is set to CONFIDENCE_MEDIUM.
     */
    let mut result = signatures::common::SignatureResult {
                                            offset: offset,
                                            description: DESCRIPTION.to_string(),
                                            confidence: signatures::common::CONFIDENCE_MEDIUM,
                                            ..Default::default()
    };

    // Parse the header, interpreting structure fields as big endian values
    if let Ok(foobar_header) = structures::common::parse(&file_data[offset..], &foobar_header_structure, "big") {

        /*
         * Do some sanity checks on the header values.
         * We already know the header's magic field matches the defined FooBar file system magic bytes, otherwise this
         * parser would have never been invoked in the first place. But, we can do some additional sanity checking to
         * help weed out false positives.
         */

        // We know that the reserved field must be 0
        if foobar_header["reserved"] == 0 {

            // We know that the flags field should only be one of these values
            if allowed_flags.contains(&foobar_header["flags"]) {
        
                // Include the size of the FooBar image in our SignatureResult structure
                // Note that no sanity check is done on this field; if a signature returns
                // a size that would extend beyond EOF, it is automatically marked as invalid
                // by binwalk::scan.
                result.size = foobar_header["image_size"];

                // This is not necessary, but it is nice to display some more detailed information about the signature to the user, if possible
                result.description = format!("{}, total size: {} bytes", result.description, result.size);

                // Everything looks ok!
                return Ok(result);
            }
        }
    }

    // Something didn't look right about this file data, it is likely a false positive, so return an error
    return Err(signatures::common::SignatureError);
}
```

#### Step 2

To make `signatures/foobar.rs` available to the rest of the Rust code, append the following line to `signatures.rs`:

```rust
pub mod foobar;
```

#### Step 3

Finally, add a new signature definition to the list of signatures defined in `magic::patterns` function:

```rust
    // FooBar file system
    binary_signatures.push(signatures::common::Signature {
                                        // A unique name for the signature, no spaces
                                        name: "foobar".to_string(),
                                        // Set to true for signatures with very short magic bytes; they will only be matched at file offset 0
                                        short: false,
                                        // Offset from the start of the file to the "magic" bytes; only relevant for short signatures
                                        magic_offset: 0,
                                        // Most signatures will want to set this to false and let the code in main.rs determine if/when to display
                                        always_display: false,
                                        // This is the function in signatures/foobar.rs that returns the FooBar magic bytes
                                        magic: signatures::foobar::foobar_magic(),
                                        // This is the parser that we wrote in signatures/foobar.rs
                                        parser: signatures::foobar::foobar_parser,
                                        // This is the human-readable description we defined in signatures/foobar.rs
                                        description: signatures::foobar::DESCRIPTION.to_string(),
                                        // We don't have an associated extractor for this file system, so set this to None
                                        extractor: None,
    });
```

Now re-compile with `cargo build --release` and the new FooBar signature should be listed in the `binwalk --list` ouput.

To define a new extractor for this file type, see: [extractors/README.md](../extractors/README.md).
