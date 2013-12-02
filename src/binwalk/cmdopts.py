# Contains all the command line options and usage output for the binwlak script.
# Placed here so that other scripts can programmatically access the command line options list (e.g., for auto-completion generation).

import os
import sys
import binwalk.config

short_options = "3AaBbCcdEeGHhIiJkLMNnOPpQqrSTtUuVvWwz?D:F:f:g:j:K:o:l:m:R:s:X:x:Y:y:Z:"
long_options = [
		"3D",
		"3d",
		"rm",
		"help",
		"green",
		"red",
		"blue",
		"examples",
		"quiet", 
		"csv",
		"verbose",
		"opcodes",
		"cast",
		"update",
		"binwalk", 
		"keep-going",
		"show-invalid",
		"show-grids",
		"ignore-time-skew",
		"honor-footers",
		"profile",
		"delay", # delay is depreciated, but kept for backwards compatability
		"skip-unopened",
		"term",
		"tim",
		"terse",
		"diff",
		"dumb",
		"entropy",
		"heuristic",
		"math",
		"gzip",
		"save-plot",
		"no-plot",
		"no-legend", 
		"strings",
		"carve",
		"weight=",
		"matryoshka=",
		"list-plugins",
		"disable-plugins",
		"disable-plugin=",
		"enable-plugin=",
		"max-size=",
		"marker=",
		"strlen=",
		"file=", 
		"block=",
		"offset=", 
		"length=", 
		"exclude=",
		"include=",
		"search=",
		"extract=",
		"dd=",
		"grep=",
		"magic=",
		"raw-bytes=",
]

def usage(fd):
	fd.write("\n")
	
	fd.write("Binwalk v%s\n" % binwalk.config.Config.VERSION)
	fd.write("Craig Heffner, http://www.devttys0.com\n")
	fd.write("\n")
	
	fd.write("Usage: %s [OPTIONS] [FILE1] [FILE2] [FILE3] ...\n" % os.path.basename(sys.argv[0]))
	fd.write("\n")
	
	fd.write("Signature Analysis:\n")
	fd.write("\t-B, --binwalk                 Perform a file signature scan (default)\n")
	fd.write("\t-R, --raw-bytes=<string>      Search for a custom signature\n")
	fd.write("\t-A, --opcodes                 Scan for executable code signatures\n")
	fd.write("\t-C, --cast                    Cast file contents as various data types\n")
	fd.write("\t-m, --magic=<file>            Specify an alternate magic file to use\n")
	fd.write("\t-x, --exclude=<filter>        Exclude matches that have <filter> in their description\n")
	fd.write("\t-y, --include=<filter>        Only search for matches that have <filter> in their description\n")
	fd.write("\t-I, --show-invalid            Show results marked as invalid\n")
	fd.write("\t-T, --ignore-time-skew        Do not show results that have timestamps more than 1 year in the future\n")
	fd.write("\t-k, --keep-going              Show all matching results at a given offset, not just the first one\n")
	fd.write("\t-b, --dumb                    Disable smart signature keywords\n")
	fd.write("\n")

	fd.write("Strings Analysis:\n")
	fd.write("\t-S, --strings                 Scan for ASCII strings (may be combined with -B, -R, -A, or -E)\n")
	fd.write("\t-s, --strlen=<n>              Set the minimum string length to search for (default: 3)\n")
	fd.write("\n")
	
	fd.write("Entropy Analysis:\n")
	fd.write("\t-E, --entropy                 Plot file entropy (may be combined with -B, -R, -A, or -S)\n")
	fd.write("\t-H, --heuristic               Identify unknown compression/encryption based on entropy heuristics (implies -E)\n")
	fd.write("\t-K, --block=<int>             Set the block size for entropy analysis (default: %d)\n" % binwalk.entropy.FileEntropy.DEFAULT_BLOCK_SIZE)
	fd.write("\t-a, --gzip                    Use gzip compression ratios to measure entropy\n")
	fd.write("\t-N, --no-plot                 Do not generate an entropy plot graph\n")
	fd.write("\t-F, --marker=<offset:name>    Add a marker to the entropy plot graph\n")
	fd.write("\t-Q, --no-legend               Omit the legend from the entropy plot graph\n")
	fd.write("\t-J, --save-plot               Save plot as a PNG (implied if multiple files are specified)\n")
	fd.write("\n")

	fd.write("Binary Visualization:\n")
	fd.write("\t-3, --3D                      Generate a 3D binary visualization\n")
	fd.write("\t-Z, --weight                  Manually set the cutoff weight (lower weight, more data points)\n")
	fd.write("\t-V, --show-grids              Display the x-y-z grids in the resulting plot\n")
	fd.write("\n")

	fd.write("Binary Diffing:\n")
	fd.write("\t-W, --diff                    Hexdump / diff the specified files\n")
	fd.write("\t-K, --block=<int>             Number of bytes to display per line (default: %d)\n" % binwalk.hexdiff.HexDiff.DEFAULT_BLOCK_SIZE)
	fd.write("\t-G, --green                   Only show hex dump lines that contain bytes which were the same in all files\n")
	fd.write("\t-i, --red                     Only show hex dump lines that contain bytes which were different in all files\n")
	fd.write("\t-U, --blue                    Only show hex dump lines that contain bytes which were different in some files\n")
	fd.write("\t-w, --terse                   Diff all files, but only display a hex dump of the first file\n")
	fd.write("\n")

	fd.write("Extraction Options:\n")
	fd.write("\t-D, --dd=<type:ext:cmd>       Extract <type> signatures, give the files an extension of <ext>, and execute <cmd>\n")
	fd.write("\t-e, --extract=[file]          Automatically extract known file types; load rules from file, if specified\n")
	fd.write("\t-M, --matryoshka=[n]          Recursively scan extracted files, up to n levels deep (8 levels of recursion is the default)\n")
	fd.write("\t-j, --max-size=<int>          Limit extracted file sizes (default: no limit)\n")      
	fd.write("\t-r, --rm                      Cleanup extracted files and zero-size files\n")
	fd.write("\t-d, --honor-footers           Only extract files up to their corresponding footer signatures\n")
	fd.write("\t-z, --carve                   Carve data from files, but don't execute extraction utilities (implies -d)\n")
	fd.write("\n")

	fd.write("Plugin Options:\n")
	fd.write("\t-X, --disable-plugin=<name>   Disable a plugin by name\n")
	fd.write("\t-Y, --enable-plugin=<name>    Enable a plugin by name\n")
	fd.write("\t-p, --disable-plugins         Do not load any binwalk plugins\n")
	fd.write("\t-L, --list-plugins            List all user and system plugins by name\n")
	fd.write("\n")

	fd.write("General Options:\n")	
	fd.write("\t-o, --offset=<int>            Start scan at this file offset\n")
	fd.write("\t-l, --length=<int>            Number of bytes to scan\n")
	fd.write("\t-g, --grep=<text>             Grep results for the specified text\n")
	fd.write("\t-f, --file=<file>             Log results to file\n")
	fd.write("\t-c, --csv                     Log results to file in csv format\n")
	fd.write("\t-O, --skip-unopened           Ignore file open errors and process only the files that can be opened\n")
	fd.write("\t-t, --term                    Format output to fit the terminal window\n")
	fd.write("\t-q, --quiet                   Supress output to stdout\n")
	fd.write("\t-v, --verbose                 Be verbose (specify twice for very verbose)\n")
	fd.write("\t-u, --update                  Update magic signature files\n")
	fd.write("\t-?, --examples                Show example usage\n")
	fd.write("\t-h, --help                    Show help output\n")
	fd.write("\n")

	if fd == sys.stderr:
		sys.exit(1)
	else:
		sys.exit(0)

