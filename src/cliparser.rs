use clap::{CommandFactory, Parser};

#[derive(Debug, Parser)]
#[command(author, version, about, long_about = None)]
pub struct CliArgs {
    /// List supported signatures and extractors
    #[arg(short = 'L', long)]
    pub list: bool,

    /// Read data from standard input
    #[arg(short, long)]
    pub stdin: bool,

    /// Supress normal stdout output
    #[arg(short, long)]
    pub quiet: bool,

    /// During recursive extraction display *all* results
    #[arg(short, long)]
    pub verbose: bool,

    /// Automatically extract known file types
    #[arg(short, long)]
    pub extract: bool,

    /// Carve both known and unknown file contents to disk
    #[arg(short, long)]
    pub carve: bool,

    /// Recursively scan extracted files
    #[arg(short = 'M', long)]
    pub matryoshka: bool,

    /// Search for all signatures at all offsets
    #[arg(short = 'a', long)]
    pub search_all: bool,

    /// Generate an entropy graph with Plotly
    #[arg(short = 'E', long, conflicts_with = "extract")]
    pub entropy: bool,

    /// Save entropy graph as a PNG file
    #[arg(short, long)]
    pub png: Option<String>,

    /// Perform a hexdump / diff of a file or files
    #[arg(short = 'W', long, conflicts_with = "list")]
    pub hexdump: bool,

    /// Only show lines containing bytes that are different among all files
    #[arg(short = 'i', long)]
    pub show_red: bool,

    /// Only show lines containing bytes that are the same among all files
    #[arg(short = 'G', long)]
    pub show_green: bool,

    /// Only show lines containing bytes that are different among some files
    #[arg(short = 'U', long)]
    pub show_blue: bool,

    /// Collapse repeated output lines
    #[arg(short = 'u', long)]
    pub show_same: bool,

    /// Diff all files, but only display a hex dump of the first file
    #[arg(short = 'w', long)]
    pub terse: bool,

    /// Set file block size (hexdump line size)
    #[arg(short = 'K', long, default_value_t = 16)]
    pub block: usize,

    /// Log JSON results to a file ('-' for stdout)
    #[arg(short, long)]
    pub log: Option<String>,

    /// Manually specify the number of threads to use
    #[arg(short, long)]
    pub threads: Option<usize>,

    /// Do no scan for these signatures
    #[arg(short = 'x', long, value_delimiter = ',', num_args = 1..)]
    pub exclude: Option<Vec<String>>,

    /// Only scan for these signatures
    #[arg(short = 'y', long, value_delimiter = ',', num_args = 1.., conflicts_with = "exclude")]
    pub include: Option<Vec<String>>,

    /// Extract files/folders to a custom directory
    #[arg(short, long, default_value = "extractions")]
    pub directory: String,

    /// Path(s) to the file(s) to analyze
    #[arg(value_name = "FILE")]
    pub files: Vec<String>,
}

pub fn parse() -> CliArgs {
    let args = CliArgs::parse();

    if std::env::args().len() == 1 {
        CliArgs::command()
            .print_help()
            .expect("Failed to print help output");
        std::process::exit(0);
    }

    args
}
