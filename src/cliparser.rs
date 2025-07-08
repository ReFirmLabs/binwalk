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

    /// Path to the file to analyze
    pub file_name: Option<String>,
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
