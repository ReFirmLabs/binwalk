# Binwalk v3

This is an updated version of the Binwalk firmware analysis tool, re-written in Rust for speed and accuracy.

![binwalk v3](images/binwalk_animated.svg)

## What does it do?

Binwalk can identify, and optionally extract, files and data that have been embedded inside of other files.

While its primary focus is firmware analysis, it supports a [wide variety](https://github.com/ReFirmLabs/binwalk/wiki/Supported-Signatures) of file and data types.

Through [entropy analysis](https://github.com/ReFirmLabs/binwalk/wiki/Generating-Entropy-Graphs), it can even help to identify unknown compression or encryption!

Binwalk can be customized and [integrated](https://github.com/ReFirmLabs/binwalk/wiki/Using-the-Rust-Library) into your own Rust projects.

## How do I get it?

The easiest way to install Binwalk and all dependencies is to [build a Docker image](https://github.com/ReFirmLabs/binwalk/wiki/Building-A-Binwalk-Docker-Image).

Or, you can [compile from source](https://github.com/ReFirmLabs/binwalk/wiki/Compile-From-Source)!

## How do I use it?

Usage is _**simple**_, analysis is _**fast**_, and results are _**detailed**_:

```
binwalk DIR-890L_AxFW110b07.bin
```
![example output](images/output.png)

Use `--help`, or check out the [Wiki](https://github.com/ReFirmLabs/binwalk/wiki#usage) for more advanced options!
