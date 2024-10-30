use clap::Parser;

#[derive(Debug, Parser)]
#[command(author, version, about, long_about = None)]
pub struct CliArgs {
    /// List supported signatures and extractors
    #[arg(short = 'L', long)]
    pub list: bool,

    /// Supress output to stdout
    #[arg(short, long)]
    pub quiet: bool,

    /// During recursive extraction display *all* results
    #[arg(short, long)]
    pub verbose: bool,

    /// Automatically extract known file types
    #[arg(short, long)]
    pub extract: bool,

    /// Recursively scan extracted files
    #[arg(short = 'M', long)]
    pub matryoshka: bool,

    /// Search for all signatures at all offsets
    #[arg(short = 'a', long)]
    pub search_all: bool,

    /// Plot the entropy of the specified file
    #[arg(short = 'E', long, conflicts_with = "extract")]
    pub entropy: bool,

    /// Log JSON results to a file
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
    #[arg(short = 'C', long, default_value = "extractions")]
    pub directory: String,

    /// Path to the file to analyze
    pub file_name: Option<String>,
}

pub fn parse() -> CliArgs {
    CliArgs::parse()
}
