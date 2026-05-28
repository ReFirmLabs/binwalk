use std::process::ExitCode;

mod binwalk;
mod common;
mod display;
mod entropy;
mod extractors;
mod json;
mod magic;
mod orchestrator;
mod signatures;
mod structures;

fn main() -> ExitCode {
    let args = orchestrator::OrchestratorArgs::new_or_help();
    orchestrator::Orchestrator::new(args).scan()
}
