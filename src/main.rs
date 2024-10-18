use binwalk::AnalysisResults;
use log::{debug, error, info};
use std::collections::VecDeque;
use std::panic;
use std::process;
use std::sync::mpsc;
use std::thread;
use std::time;
use threadpool::ThreadPool;

mod binwalk;
mod cliparser;
mod common;
mod display;
mod entropy;
mod extractors;
mod json;
mod magic;
mod signatures;
mod structures;

fn main() {
    // Only use one thread if unable to auto-detect available core info
    const DEFAULT_WORKER_COUNT: usize = 1;

    // Number of seconds to wait before printing debug progress info
    const PROGRESS_INTERVAL: u64 = 30;

    // Output directory for extracted files
    let mut output_directory: Option<String> = None;

    /*
     * Maintain a queue of files waiting to be analyzed.
     * Note that ThreadPool has its own internal queue so this may seem redundant, however,
     * queuing a large number of jobs via the ThreadPool queue results in *massive* amounts
     * of unecessary memory consumption, especially when recursively analyzing many files.
     */
    let mut target_files = VecDeque::new();

    // Statistics variables; keeps track of analyzed file count and total analysis run time
    let mut file_count: usize = 0;
    let run_time = time::Instant::now();
    let mut last_progress_interval = time::Instant::now();

    // Initialize logging
    env_logger::init();

    // Process command line aguments
    let cliargs = cliparser::parse();

    // If --list was specified, just display a list of signatures and return
    if cliargs.list == true {
        display::print_signature_list(cliargs.quiet, &magic::patterns());
        return;
    }

    // If --list was not specified, a target file must be provided
    if cliargs.file_name.is_none() {
        panic!("No target file name specified! Try --help.");
    }

    // If entropy analysis was requested, generate the entropy graph and return
    if cliargs.entropy == true {
        display::print_plain(cliargs.quiet, "Calculating file entropy...");

        if let Ok(entropy_results) = entropy::plot(cliargs.file_name.unwrap()) {
            // Log entropy results to JSON file, if requested
            json::log(
                &cliargs.log,
                json::JSONType::Entropy(entropy_results.clone()),
            );

            display::print_plain(cliargs.quiet, "entropy graph saved to: ");
            display::println_plain(cliargs.quiet, &entropy_results.file);
        } else {
            panic!("Entropy analysis failed!");
        }

        return;
    }

    // If extraction was requested, we need to initialize the output directory
    if cliargs.extract == true {
        output_directory = Some(cliargs.directory);
    }

    // Initialize binwalk
    let binwalker = binwalk::Binwalk::configure(
        cliargs.file_name,
        output_directory,
        cliargs.include,
        cliargs.exclude,
        None,
    )
    .expect("Binwalk initialization failed");

    // If the user specified --threads, honor that request; else, auto-detect available parallelism
    let available_workers = cliargs.threads.unwrap_or_else(|| {
        // Get CPU core info
        match thread::available_parallelism() {
            // In case of error use the default
            Err(e) => {
                error!("Failed to retrieve CPU core info: {e}");
                DEFAULT_WORKER_COUNT
            }
            Ok(coreinfo) => coreinfo.get(),
        }
    });

    // Sanity check the number of available worker threads
    if available_workers < 1 {
        panic!("No available worker threads!");
    }

    // Initialize thread pool
    debug!(
        "Initializing thread pool with {} workers",
        available_workers
    );
    let workers = ThreadPool::new(available_workers);
    let (worker_tx, worker_rx) = mpsc::channel();

    /*
     * Set a custom panic handler.
     * This ensures that when any thread panics, the default panic handler will be invoked
     * _and_ the entire process will exit with an error code.
     */
    let default_panic_handler = panic::take_hook();
    panic::set_hook(Box::new(move |panic_info| {
        default_panic_handler(panic_info);
        process::exit(-1);
    }));

    debug!(
        "Queuing initial target file: {}",
        binwalker.base_target_file
    );

    // Queue the initial file path
    target_files.insert(target_files.len(), binwalker.base_target_file.clone());

    /*
     * Main loop.
     * Loop until all pending thread jobs are complete and there are no more files in the queue.
     */
    while target_files.is_empty() == false || workers.active_count() > 0 {
        // If there are files waiting to be analyzed and there is at least one free thread in the pool
        if target_files.is_empty() == false && workers.active_count() < workers.max_count() {
            // Get the next file path from the target_files queue
            let target_file = target_files
                .pop_front()
                .expect("Failed to retrieve next file from the queue");

            // Spawn a new worker for the new file
            spawn_worker(
                &workers,
                binwalker.clone(),
                target_file,
                cliargs.extract,
                worker_tx.clone(),
            );
        }

        // Don't spin CPU cycles if there is no backlog of files to analyze
        if target_files.is_empty() == true {
            let sleep_time = time::Duration::from_millis(1);
            thread::sleep(sleep_time);
        }

        // Some debug info on analysis progress
        if last_progress_interval.elapsed().as_secs() >= PROGRESS_INTERVAL {
            info!(
                "Status: active worker threads: {}/{}, files waiting in queue: {}",
                workers.active_count(),
                workers.max_count(),
                target_files.len()
            );
            last_progress_interval = time::Instant::now();
        }

        // Get response from a worker thread, if any
        if let Ok(results) = worker_rx.try_recv() {
            // Keep a tally of how many files have been analyzed
            file_count += 1;

            // Log analysis results to JSON file
            json::log(&cliargs.log, json::JSONType::Analysis(results.clone()));

            // Nothing found? Nothing else to do for this file.
            if results.file_map.len() == 0 {
                debug!("Found no results for file {}", results.file_path);
                continue;
            }

            // Print analysis results to screen
            if should_display(&results, file_count, cliargs.verbose) == true {
                display::print_analysis_results(cliargs.quiet, cliargs.extract, &results);
            }

            // If running recursively, add extraction results to list of files to analyze
            if cliargs.matryoshka {
                for (_signature_id, extraction_result) in results.extractions.into_iter() {
                    if extraction_result.do_not_recurse == false {
                        for file_path in extractors::common::get_extracted_files(
                            &extraction_result.output_directory,
                        ) {
                            debug!("Queuing {file_path} for analysis");
                            target_files.insert(target_files.len(), file_path.clone());
                        }
                    }
                }
            }
        }
    }

    // All done, show some basic statistics
    display::print_stats(
        cliargs.quiet,
        run_time,
        file_count,
        binwalker.signature_count,
        binwalker.patterns.len(),
    );
}

/// Returns true if the specified results should be displayed to screen
fn should_display(results: &AnalysisResults, file_count: usize, verbose: bool) -> bool {
    let mut display_results: bool = false;

    /*
     * For brevity, when analyzing more than one file only display subsequent files whose results
     * contain signatures that we always want displayed, or which contain extractable signatures.
     * This can be overridden with the --verbose command line flag.
     */
    if file_count == 1 || verbose == true {
        display_results = true;
    } else {
        if results.extractions.len() > 0 {
            display_results = true;
        } else {
            for signature in &results.file_map {
                if signature.always_display == true {
                    display_results = true;
                    break;
                }
            }
        }
    }

    return display_results;
}

/// Spawn a worker thread to analyze a file
fn spawn_worker(
    pool: &ThreadPool,
    bw: binwalk::Binwalk,
    target_file: String,
    do_extraction: bool,
    worker_tx: mpsc::Sender<AnalysisResults>,
) {
    pool.execute(move || {
        // Analyze target file, with extraction, if specified
        let results = bw.analyze(&target_file, do_extraction);
        // Report file results back to main thread
        if let Err(e) = worker_tx.send(results) {
            panic!(
                "Worker thread for {target_file} failed to send results back to main thread: {e}"
            );
        }
    });
}
