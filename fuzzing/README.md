# Fuzzing Binwalk

Fuzz testing for Binwalk is done through [AFL++](https://aflplus.plus).

At the moment code coverage is not 100% complete, but exercises the file parsing code, which is the most problematic and error-prone.

## Fuzzer Dependencies

You must have a C compiler and `make` installed, as well as the `cargo-afl` crate:

```
sudo apt install build-essentials
cargo install cargo-afl
```

## Building the Fuzzer

```
cargo afl build --release
```

## Running the Fuzzer

You must provide an input directory containing sample files for the fuzzer to mutate.

You must provide an output directory for the fuzzer to save crash results to.

```
cargo afl fuzz -i input_directory -o output_directory ./target/release/fuzz
```
