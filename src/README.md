# Code Overview

This is a high-level overview of the Binwalk code structure and functionality.

The code can generally be broken down into four categories:

- [Core code](#core-code)
- [Structure code](#structure-code)
- [Signature code](#signature-code)
- [Extractor code](#extractor-code)

## Core Code

### main.rs

This is main(). It:

- Manages and distributes analysis jobs to the thread pool
- Queues extracted files for analysis
- Decides what to display to screen
- Logs JSON results to disk

### worker.rs

This is the "worker thread" code; workers are available to receive jobs via the thread pool. Each worker thread:

- Reads a single file into memory
- Performs a binwalk scan on the file contents
- Sends scan results to the binwalk extractor for extraction
- Returns an `AnalysisResults` structure back to main()

The `AnalysisResults` strucuture is JSON serializable and includes the name of the file that was analyzed,
information about all the signatures identified in the file and any extraction results.

Note that results are not reported until all analysis and extraction has been completed for the file under analysis.

### binwalk.rs

This is where much of the heavy lifting takes place. It is broken into three parts:

#### binwalk::init
- Loads all the "magic" patterns identified by each signature definition
- If extraction is enabled, initializes the extraction output directory
- Creates a symlink in the output directory pointing to the file specified on the command line
- Generates lookup tables for matching magic patterns to their corresponding signatures, and signatures to their corresponding extractors

#### binwalk::scan
- Scans a file for said "magic" patterns, invoking each signature's corresponding parser function to parse and validate each magic pattern match
- Sorts results and invalidates conflicting results
- If a parser is unable to report the size of its data, the data is assumed to extend to the next signature (with a confidence of `medium` or higher) or EOF, whichever comes first
- The Aho-Corasick algorithm is used for magic pattern matching, which searches the file data for *all* magic patterns at once

#### binwalk::extract
- Executes extractors for all signatures identified by `binwalk::scan` which have a corresponding extractor
- If extraction fails and the signature reported that it ended before EOF, it attempts extraction again, this time with the signature size extended to EOF


### display.rs

This is the only place where data is printed to stdout. It:

- Colorizes output text
- Formats output to fit the terminal

Note that this code does not handle any errors, warnings, or debug info; these are all send to stderr via the `env_logger` crate.

### magic.rs

This code defines a list of all supported signatures, specifically a list of `signatures::common::Signature` structures.
Each entry in this list defines a unique name, the signature's "magic" patterns, a brief description, and which parser/extractor to use.

The signature parsers themselves are located in the [signatures](#signature-code) directory, while extractors can be found in the
[extractors](#extractor-code) directory.

### entropy.rs

This code is repsonsible for performing entropy analysis of a file and generating an entropy graph via the [plotters](https://docs.rs/plotters/latest/plotters/) crate.

The output graph will be saved as a PNG to the current working directory.

The `entropy::FileEntropy` structure returned by `entropy::plot` is JSON serializable so that raw entropy analysis results can be
saved to a JSON file.

### json.rs

This code is repsonsible for converting `worker::AnalysisResults` and `entropy::FileEntropy` structures to JSON and writing them to disk.
Most of the heavy lifting is taken care of by `serde`.

Note that the JSON output will be a list of JSON structures; each one is written to disk as soon as it is reported.
Currently, this requires overwriting the terminating array and appending the new JSON data in the JSON output file in order for the JSON
file to be valid JSON; this makes it unsuitable for streaming to sockets, stdout, etc.

### cliparser.rs

Defines and parses command line options via the `clap` crate.

### common.rs

Contains common functions used throughout the code:

- `common::cr32`
- `common::read_file`
- `common::get_cstring`
- `common::epoch_to_string`

## Structure Code

The code in the `structures` directory is responsible for parsing the data structures of various file formats.
They may be used by either signatures or internal extractors as needed.

Note that these structure parsers typically only process just enough data to get the job done (i.e., validate a signature match
or extract files/data), and many only parse partial data structures.

### structures/common.rs

Provides confenience functions to support the parsing of basic data structures, specifically:

- `structure::size`
- `structure::parse`

Structures are defined as vectors of tuples, and returned as HashMaps.

See [structures/README.md](structures/README.md) for additional details on defining file signatures and writing parsers.

## Signature Code

The code in the `signatures` directory is responsible for parsing and validating "magic byte" matches found inside a target file.
By convention, these "magic bytes" are defined here as well.

Each signature must be loaded into the signature list defined in `magic.rs`.

### signatures/common.rs

Contains common definitions and structures used by file signatures. 

Each file signature is defined by a `signatures::common::Signature` structure in `magic.rs`. This structure includes important signature
attributes, such as the signature name and description, the "magic bytes" associated with the signature, which parser to use for
signature validation, and which extractor to use (if any) for extraction.

Signature parsers are functions of type `signatures::common::SignatureParser`. They are provided full access to the file data, and
an offset into the file data where the signature's "magic bytes" were located. Parsers are responsible for parsing and validating
file signatures, and must return a `signatures::common::SignatureResult` structure on success, or a `signatures::common::SignatureError`
on failure.

The three confidence levels reported in a `SignatureResult` structure are also defined here:

- `signatures::common::CONFIDENCE_LOW`
- `signatures::common::CONFIDENCE_MEDIUM`
- `signatures::common::CONFIDENCE_HIGH`

See [signatures/README.md](signatures/README.md) for additional details on defining file signatures and writing parsers.

## Extractor Code

The code in the `extractors` directory is responsible for defining file extractors.

Each extractor is assigned to a particular signature in `magic.rs`.

### extractors/common.rs

Contains definitions and helper functions used by `binwalk::extract` and file extractors.

Extractors may be internal or external.

Both internal and external extractors are defined by an `extractors::common::Extractor` structure, which includes which internal/external
extractor to use, if the files extracted by the extractor should be included for analysis during recursive extraction, and for external
extractors, what command line options to supply and which exit codes are considered successful.

Extractors return a `extractors::common::ExtractionResult` structure upon completion.

Each extractor is associated with a correponding signature via the `signatures::common::Signature` structures defined in `magic.rs`.
Some extractors support multiple file types, so one extractor may be associated with multiple signatures.

Some conveience functions are also available, and used by various internal extractors:

- `extractors::common::safe_path_join`
- `extractors::common::create_file`
- `extractors::common::create_symlink`
- `extractors::common::create_directory`
- `extractors::common::make_executable`

See [extractors/README.md](extractors/README.md) for additional details on writing and defining file extractors.
