use log::{debug, error};
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

    let binwalker: binwalk::Binwalk;
    let mut output_directory: Option<String> = None;

    // Statistics variables; keeps track of analyzed file count and total analysis run time
    let mut file_count: usize = 0;
    let run_time = time::Instant::now();

    // Boolean flag to indicate if a result should be displayed to screen or not
    let mut display_results: bool;

    // Queue of files to be analyzed
    let mut target_files = VecDeque::new();

    // Thread pool related variables
    let mut pending_jobs = 0;
    let mut available_workers = DEFAULT_WORKER_COUNT;

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
    match binwalk::Binwalk::new(
        cliargs.file_name,
        output_directory,
        cliargs.include,
        cliargs.exclude,
        None,
    ) {
        Err(_) => {
            panic!("Binwalk initialization failed");
        }
        Ok(bw) => {
            binwalker = bw;
        }
    }

    // If the user specified --threads, honor that request; else, auto-detect available parallelism
    match cliargs.threads {
        Some(threads) => {
            available_workers = threads;
        }
        None => {
            // Get CPU core info
            match thread::available_parallelism() {
                Err(e) => error!("Failed to retrieve CPU core info: {}", e),
                Ok(coreinfo) => available_workers = coreinfo.get(),
            }
        }
    }

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

    // Queue the specified file for analysis
    debug!(
        "Queuing initial target file: {}",
        binwalker.base_target_file
    );
    target_files.insert(target_files.len(), binwalker.base_target_file.clone());

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

    /*
     * Main loop.
     * Loop until all pending thread jobs are complete and there are no more files in the queue.
     */
    while target_files.is_empty() == false || pending_jobs > 0 {
        // If there are files in the queue and there is at least one worker not doing anything
        if target_files.is_empty() == false && pending_jobs < available_workers {
            // Get the next file in the list
            let target_file = target_files
                .pop_front()
                .expect("Failed to retrieve the name of the next file to scan");

            // Clone the transmit channel so the worker thread can send response data back to this main thread
            let worker_tx = worker_tx.clone();

            // Clone binwalk config data for worker thread
            let binworker = binwalker.clone();

            /* Start of worker thread code */
            workers.execute(move || {
                // Analyze target file, with extraction, if specified
                let results = binworker.analyze(&target_file, cliargs.extract);
                // Report file results back to main thread
                if let Err(e) = worker_tx.send(results) {
                    panic!(
                        "Worker thread for {} failed to send results back to main thread: {}",
                        target_file, e
                    );
                }
            });
            /* End of worker thread code */

            // Increment pending jobs counter
            pending_jobs += 1;
        }

        // Don't let the main loop eat up CPU cycles if there's no back log of work to be done
        if target_files.is_empty() == true {
            let sleep_time = time::Duration::from_millis(1);
            thread::sleep(sleep_time);
        }

        // If there are pending jobs, check to see if any have responded with some results
        if pending_jobs > 0 {
            // Read in analysis results from a worker thread
            if let Ok(results) = worker_rx.try_recv() {
                // If we got some results that means a worker thread has completed, decrement pending jobs counter
                pending_jobs -= 1;

                // Keep a tally of how many files have been analyzed
                file_count += 1;

                // Log analysis results to JSON file
                json::log(&cliargs.log, json::JSONType::Analysis(results.clone()));

                // Nothing found? Nothing else to do for this file.
                if results.file_map.len() == 0 {
                    debug!("Found no results for file {}", results.file_path);
                    continue;
                }

                /*
                 * For brevity, when analyzing more than one file only display subsequent files whose results
                 * contain signatures that we always want displayed, or which contain extractable signatures.
                 * This can be overridden with the --verbose command line flag.
                 */
                if file_count == 1 || cliargs.verbose == true {
                    display_results = true;
                } else {
                    display_results = false;

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

                // Print signature & extraction results
                if display_results == true {
                    display::print_analysis_results(cliargs.quiet, &results);
                }

                // If running recursively, add extraction results to list of files to analyze
                if cliargs.matryoshka {
                    for (_signature_id, extraction_result) in results.extractions.into_iter() {
                        if extraction_result.do_not_recurse == false {
                            for file_path in extractors::common::get_extracted_files(
                                &extraction_result.output_directory,
                            ) {
                                debug!("Queuing {} for analysis", file_path);
                                target_files.insert(target_files.len(), file_path.clone());
                            }
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
