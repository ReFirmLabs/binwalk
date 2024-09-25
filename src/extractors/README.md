# Creating Extractors

There are three steps to defining a new extractor:

1. Create a new `.rs` file in the `extractors` directory and write an extractor definition
2. Import the new `.rs` file by adding it to the `extractors.rs` file
3. Update the relevent signature definitions in `magic.rs` to use the new extractor

## Writing an Extractor Definition

Extractors can be either internal (native Rust code compiled into Binwalk) or external (external command line utilities).
In either case, each extractor must be defined via a `extractors::common::Extractor` structure.

### External Extractors

External extractor definitions describe:

- The name of a command-line utility to run
- What arguments to pass to it
- What file extension the utility expects
- Which exit codes are considered successful (the default is exit code `0`)

### Internal Extractors

Internal extractor definitions need only specify the internal extractor function to call. This function must conform
to the `extractors::common::InternalExtractor` type definition.

The extraction function will be passed:

- The entirety of the file data
- An offset inside the file data at which to begin processing data
- An output directory (optional)

If the output directory is `None`, the extractor function should perform a "dry run", processing the intended file format
as normal, but not extract any data; this allows signatures to use the extractor function to validate potential signature
matches without performing an actual extraction.

The `extractors::common` API functions *should* be used for the creation of files/symlinks/directories, constructing file paths, etc.
These functions protect against common path traversal attacks by ensuring that paths are not created outside of the specified "chroot directory":

- `create_file`
- `create_fifo`
- `create_socket`
- `chrooted_path`
- `append_to_file`
- `create_symlink`
- `safe_path_join`
- `make_executable`
- `create_directory`
- `create_block_device`
- `create_character_device`

Internal extractors must return an `extractors::common::ExtractionResult` struct.

## Example

We want to define an extractor for a new, contrived, file type, `FooBar file system`. We will look at two examples, one
in which we execute an external utility, `unfoobar`, and one in which we define an internal extractor to extract the
file system contents.

The `unfoobar` utility is typically executed on the command line like:

```bash
unfoobar -x -o foobar-root -f input_file.bin
```

### Step 1

Create a new file, `extractors/foobar.rs`, with the following contents:

```rust
use crate::extractors;

/*
 * This function returns an instance of extractors::common::Extractor, which
 * describes how to run the unfoobar utility. It will be added to the Signature
 * entry in magic.rs.
 */
pub fn foobar_extractor() -> extractors::common::Extractor {
    // Build and return the Extractor struct
    return extractors::common::Extractor {
        // This indicates that we are defining an external extractor, named 'unfoobar'
        utility: extractors::common::ExtractorType::External("unfoobar".to_string()),
        // This is the file extension to use when carving the FooBar file system data to disk
        extension: "bin".to_string(),
        // These are the arguments to pass to the unfoobar utility
        arguments: vec![
            "-x".to_string(),           // This option tells unfoobar to extract the file system
            "-o".to_string(),           // Specify an output directory
            "foobar-root".to_string(),  // The output directory name
            "-f".to_string(),           // Specify an input file
            // This is a special string that will be replaced at run-time with the name of the source file
            extractors::common::SOURCE_FILE_PLACEHOLDER.to_string()
        ],
        // The only valid exit code for this utility is 0
        exit_codes: vec![0],
        ..Default::default()
    };
}
```

Alternatively, you may write your own internal extractor from scratch. Writing your own extractor from scratch takes
longer than just defining an external extractor, but internal extractors have several advantages:

- They are generally faster, since input data to the extractor does not need to be carved to disk
- They *can* be made safer, as they are written in Rust and can take advantage of internal safe APIs
- Signatures can tell internal extractors to perform a "dry run", where the extractor parses the file data, but does not perform any extraction;
if the dry run is successful, then the signature code can almost certianly be assured that the data it is inspecting is a true positive

The definition for an internal extractor is simpler, but then of course you have to write the extractor code too:

```rust
use log::debug;
use crate::extractors;

/*
 * This function returns an instance of extractors::common::Extractor, which
 * specifies that an internal extractor function, extract_foobar, should be called
 * to perform extraction. It will be added to the Signature entry in magic.rs.
 */
pub fn foobar_extractor() -> extractors::common::Extractor {
    // Build and return the Extractor struct
    return extractors::common::Extractor {
        // All we need to specify is the internal extractor function, use defaults for everything else
        utility: extractors::common::ExtractorType::Internal(extract_foobar),
        ..Default::default() 
    };
}

/*
 * This is the internal extraction function.
 * Extraction details will be very specific to the file format of course, and this code is not complete.
 * It merely serves as an exemplar template.
 */
pub fn extract_foobar(file_data: &Vec<u8>, offset: usize, output_directory: Option<&String>) -> extractors::common::ExtractionResult {
    /*
     * Create the ExtractionResult return value, with defaults.
     * By default, ExtractionResult.success will be false; if extraction is successful, this must be set to true.
     * By default, ExtractionResult.size will be None; if the size of consumed data is known, this field should be updated.
     */
    let mut result = extractors::common::ExtractionResult { ..Default::default() };

    /*
     * Parse FooBar file system data.
     * If parsing is successful populate result.success and result.size fields.
     * If output_directory is None, just return; else, do the actual extraction.
     */
    
    return result;
}
```

### Step 2

To make `extractors/foobar.rs` available to the rest of the Rust code, append the following line to `extractors.rs`:

```rust
pub mod foobar;
```

### Step 3

Modify the FooBar signature definition in `magic.rs` to use the defined extractor:

```rust
    // FooBar file system
    binary_signatures.push(signatures::common::Signature {
                                        name: "foobar".to_string(),
                                        short: false,
                                        always_display: false,
                                        magic: signatures::foobar::foobar_magic(),
                                        parser: signatures::foobar::foobar_parser,
                                        description: signatures::foobar::DESCRIPTION.to_string(),
                                        // Call the function in extractors/foobar.rs that returns the Extractor structure
                                        extractor: Some(extractors::foobar::foobar_extractor()),
    });
```

Now re-compile with `cargo build --release` and the new FooBar extractor should be listed in the `binwalk --list` ouput.
