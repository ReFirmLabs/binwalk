# Binwalk Dependencies

These scripts install the required Binwalk build and runtime system dependencies, except for the Rust compiler itself.

Execute the appropriate script for your operating system (e.g., `ubuntu.sh` for Ubuntu).

## ubuntu.sh

This script installs *all* required dependencies for Ubuntu-based systems, including the dependencies listed in `pip.sh` and `src.sh`.

This should work for most Debian / Debian-based systems as well, but is only tested on Ubuntu.

## pip.sh

This script installs all Python-based dependencies via `pip3`.

It should be sourced by higher-level scripts (e.g., `ubuntu.sh`).

## src.sh

This script builds and installs all source-based dependencies.

It should be sourced by higher-level scripts (e.g., `ubuntu.sh`).
