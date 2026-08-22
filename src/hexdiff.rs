//! Hexdump and diff functionality for comparing binary files.

use colored::Colorize;
use std::io::IsTerminal;

/// Classification of a byte position when comparing across multiple files.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ByteClass {
    /// All files have the same byte value at this position.
    Green,
    /// Some files match, others differ (mixture).
    Blue,
    /// All files have distinct values at this position.
    Red,
}

impl ByteClass {
    fn to_colored_hex(self, hex: &str) -> colored::ColoredString {
        match self {
            ByteClass::Green => hex.green(),
            ByteClass::Blue => hex.blue(),
            ByteClass::Red => hex.red(),
        }
    }

    fn to_colored_ascii(self, ascii: &str) -> colored::ColoredString {
        // Keep ASCII formatting consistent with hex formatting
        self.to_colored_hex(ascii)
    }
}

/// Options for controlling hexdump/diff output.
#[derive(Debug, Clone)]
pub struct HexdiffOptions {
    /// Number of bytes per line (default: 16).
    pub block: usize,
    /// Show lines containing bytes that differ among all files.
    pub show_red: bool,
    /// Show lines containing bytes that are the same among all files.
    pub show_green: bool,
    /// Show lines containing bytes that differ among some files.
    pub show_blue: bool,
    /// Only display the first file's hex dump (but still diff against all).
    pub terse: bool,
    /// Collapse repeated identical lines (classic hexdump `*` style).
    pub collapse_repeats: bool,
}

impl Default for HexdiffOptions {
    fn default() -> Self {
        Self {
            block: 16,
            show_red: true,
            show_green: true,
            show_blue: true,
            terse: false,
            collapse_repeats: false,
        }
    }
}

#[derive(Debug, Clone)]
struct RenderedLine {
    /// Raw (non-colored) content of this line, used for collapse-repeat logic.
    raw: String,
    /// Colored/pretty output.
    display: String,
    has_red: bool,
    has_green: bool,
    has_blue: bool,
}


/// Classify a byte position across all files.
///
/// - Green: all files have the same byte (including the same EOF condition, though we don't emit
///   fully-EOF lines)
/// - Red: every file's value at this offset is distinct (e.g., A/B/C for 3 files, or A/EOF for 2)
/// - Blue: mixture (some equal, some different)
pub fn classify_position(values: &[Option<u8>]) -> ByteClass {
    let mut unique: Vec<Option<u8>> = Vec::new();
    for v in values {
        if !unique.contains(v) {
            unique.push(*v);
        }
    }

    if unique.len() <= 1 {
        ByteClass::Green
    } else if unique.len() == values.len() {
        ByteClass::Red
    } else {
        ByteClass::Blue
    }
}

/// Classify a block of bytes across 1+ files starting at `offset`.
///
/// Missing data (EOF) is treated as `None`, which participates in the comparison.
#[allow(dead_code)] // Used by tests
pub fn classify_block(files: &[&[u8]], offset: usize, block: usize) -> Vec<ByteClass> {
    let mut classes: Vec<ByteClass> = Vec::with_capacity(block);

    for i in 0..block {
        let absolute = offset + i;
        let mut values: Vec<Option<u8>> = Vec::with_capacity(files.len());
        for data in files {
            values.push(data.get(absolute).copied());
        }
        classes.push(classify_position(&values));
    }

    classes
}

/// Returns (has_red, has_green, has_blue) for a classified block/line.
#[allow(dead_code)] // Used by tests
pub fn flags_for_classes(classes: &[ByteClass]) -> (bool, bool, bool) {
    let mut has_red = false;
    let mut has_green = false;
    let mut has_blue = false;

    for c in classes {
        match c {
            ByteClass::Red => has_red = true,
            ByteClass::Green => has_green = true,
            ByteClass::Blue => has_blue = true,
        }
    }

    (has_red, has_green, has_blue)
}

/// Decide if a line should be displayed given diff flags and the selected filters.
pub fn should_display_flags(
    (has_red, has_green, has_blue): (bool, bool, bool),
    opts: &HexdiffOptions,
) -> bool {
    (opts.show_red && has_red) || (opts.show_green && has_green) || (opts.show_blue && has_blue)
}

fn is_printable_ascii(b: u8) -> bool {
    // Standard printable ASCII: '!' (0x21) through '~' (0x7E)
    // Excludes space and all control characters (0x00-0x1F) which can break terminal output
    (0x21..=0x7E).contains(&b)
}

fn render_header(file_names: &[String], block: usize, terse: bool) -> String {
    let mut out = String::new();
    out.push_str("OFFSET      ");

    // Match legacy width: (block * 4) + 2
    let header_width = (block * 4) + 2;
    let count = if terse { 1 } else { file_names.len() };
    for i in 0..count {
        let name = &file_names[i];
        out.push_str(&format!("{name:<header_width$}   "));
    }
    out.push('\n');
    out
}

fn render_line(
    offset: usize,
    files: &[(String, Vec<u8>)],
    block: usize,
    terse: bool,
) -> RenderedLine {
    let file_count = files.len();

    // Collect per-position class (global) and per-file values
    let mut classes: Vec<ByteClass> = Vec::with_capacity(block);
    let mut values: Vec<Vec<Option<u8>>> = vec![Vec::with_capacity(block); file_count];

    for i in 0..block {
        let absolute = offset + i;
        let mut at_pos: Vec<Option<u8>> = Vec::with_capacity(file_count);
        for (_name, data) in files.iter() {
            at_pos.push(data.get(absolute).copied());
        }

        let class = classify_position(&at_pos);
        classes.push(class);

        for (fidx, v) in at_pos.into_iter().enumerate() {
            values[fidx].push(v);
        }
    }

    let mut has_red = false;
    let mut has_green = false;
    let mut has_blue = false;
    for c in &classes {
        match c {
            ByteClass::Red => has_red = true,
            ByteClass::Green => has_green = true,
            ByteClass::Blue => has_blue = true,
        }
    }

    let mut raw = String::new();
    let mut display = String::new();

    // Offset format: 0x%.8X (legacy)
    raw.push_str(&format!("0x{offset:08X}    "));
    display.push_str(&format!("0x{offset:08X}    "));

    let count = if terse { 1 } else { file_count };
    for fidx in 0..count {
        let mut hex_raw = String::new();
        let mut ascii_raw = String::new();

        let mut hex_disp = String::new();
        let mut ascii_disp = String::new();

        for i in 0..block {
            let v = values[fidx][i];
            let class = classes[i];

            let (hex2, asc1) = match v {
                None => ("XX".to_string(), ".".to_string()),
                Some(b) => {
                    let hex2 = format!("{b:02X}");
                    let asc1 = if is_printable_ascii(b) {
                        (b as char).to_string()
                    } else {
                        ".".to_string()
                    };
                    (hex2, asc1)
                }
            };

            hex_raw.push_str(&hex2);
            hex_raw.push(' ');
            ascii_raw.push_str(&asc1);

            hex_disp.push_str(&class.to_colored_hex(&hex2).to_string());
            hex_disp.push(' ');
            ascii_disp.push_str(&class.to_colored_ascii(&asc1).to_string());
        }

        raw.push_str(&format!("{hex_raw}|{ascii_raw}|"));
        display.push_str(&format!("{hex_disp}|{ascii_disp}|"));

        if fidx + 1 != count {
            raw.push_str("  ");
            display.push_str("  ");
        }
    }

    RenderedLine {
        raw,
        display,
        has_red,
        has_green,
        has_blue,
    }
}

fn should_show_line(line: &RenderedLine, opts: &HexdiffOptions) -> bool {
    should_display_flags((line.has_red, line.has_green, line.has_blue), opts)
}

/// Render a hexdump/diff for one or more input files.
///
/// When a single file is provided, produces a standard hexdump.
/// When multiple files are provided, produces a side-by-side diff with
/// color-coded bytes indicating matches (green), partial matches (blue),
/// or all-different (red).
///
/// Colors are automatically disabled when stdout is not a terminal.
pub fn run(
    quiet: bool,
    inputs: Vec<(String, Vec<u8>)>,
    mut opts: HexdiffOptions,
) -> Result<(), String> {
    if quiet {
        return Ok(());
    }

    // Disable colors when stdout is not a terminal (e.g., piping to less/grep/file)
    if !std::io::stdout().is_terminal() {
        colored::control::set_override(false);
    }

    if inputs.is_empty() {
        return Err("No inputs provided".to_string());
    }

    if opts.block == 0 {
        opts.block = 16;
    }

    // If no filters specified, show everything.
    if !opts.show_red && !opts.show_green && !opts.show_blue {
        opts.show_red = true;
        opts.show_green = true;
        opts.show_blue = true;
    }

    let max_len = inputs.iter().map(|(_n, d)| d.len()).max().unwrap_or(0);
    let file_names: Vec<String> = inputs.iter().map(|(n, _d)| n.clone()).collect();

    print!("{}", render_header(&file_names, opts.block, opts.terse));

    let mut previous_raw: Option<String> = None;
    let mut in_repeat = false;

    let mut offset = 0usize;
    while offset < max_len {
        let line = render_line(offset, &inputs, opts.block, opts.terse);

        if !should_show_line(&line, &opts) {
            offset = offset.saturating_add(opts.block);
            continue;
        }

        // Collapse repeated lines (classic hexdump style)
        if opts.collapse_repeats {
            if let Some(prev) = &previous_raw {
                if *prev == line.raw {
                    if !in_repeat {
                        println!("*");
                        in_repeat = true;
                    }
                    offset = offset.saturating_add(opts.block);
                    continue;
                }
            }
        }

        in_repeat = false;
        previous_raw = Some(line.raw.clone());
        println!("{}", line.display);

        offset = offset.saturating_add(opts.block);
    }

    Ok(())
}
