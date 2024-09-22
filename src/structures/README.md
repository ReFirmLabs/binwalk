# Parsing Data Structures

Both signatures and internal extractors may need to parse data structures used by various file formats.
Structure parsing code is placed in the `structures` sub-module, as a centralized location.

## Helper Functions

There are some definitions and helper functions in `structures::common` that are generally helpful for processing data structures.

The `structures::common::parse` function provides a way to parse basic data structures by defining the data structure format,
the endianness to use, and the data to cast the structure over. It is heavily used by most structure parsers.
It supports the following data types:

- u8
- u16
- u24
- u32
- u64

Regardless of the data type specified, all values are returned as `usize` types.

The `structures::common::size` function is a convenience function that returns the number of bytes required to parse a defined data structure.

The `structures::common::StructureError` struct is typically used by structure parsers to return an error.

## Writing a Structure Parser

Structure parsers may be defined however they need to be; there are no strict rules here.
Generally, however, they should:

- Accept some data to parse
- Parse the data structure
- Validate the structure fields for correctness
- Return an error or success status

### Example

Let's write a parser for a fictional, simple, data structure:

```rust
use log::debug;
use crate::structures;
use crate::common::crc32;

/*
 * This function parses the file structure as defined in my_struct.
 * It returns the size reported in the data structure on success.
 * It returns structures::common::StructureError on failure.
 */
fn parse_my_structure(data: &[u8]) -> Result<usize, structures::common::StructureError> {
    // The header CRC is calculated over the first 15 bytes of the header
    const CRC_CALC_LEN: usize = 15;

    // Define a data structure; structure members must be in the order in which they appear in the data
    let my_struct = vec![
        ("magic", "u32"),
        ("flags", "u8"),
        ("size", "u64"),
        ("volume_id", "u16"),
        ("header_crc", "u32"),
    ];

    // Get the total size of my_struct
    let my_struct_size: usize = structures::common::size(&my_struct);

    // It is up to the caller to ensure that the defined structure fits in the provided data; if not, structures::common::parse will panic.
    if data.len() >= my_struct_size {

        // Parse the provided data in accordance with the layout defined in my_struct, interpret fields as little endian
        let parsed_structure = structures::common::parse(&data[0..my_struct_size], &my_struct, "little");
        
        // Validate the header CRC
        if parsed_structure["header_crc"] == crc32(&data[0..CRC_CALC_LEN]) as usize {
            return Ok(parsed_structure["size"]);
        }
    }

    return Err(structures::common::StructureError);
}
```

By convention, the above code would be placed in a new file, `structures/mystruct.rs`.

To import this new code into the Rust project, append the following line to `structures.rs`:

```rust
pub mod mystruct;
```

The parser function can then be accessed by any other code in the project via `structures::mystruct::parse_my_structure`.
