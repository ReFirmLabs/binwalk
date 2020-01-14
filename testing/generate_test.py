#!/usr/bin/env python
# Automatically generates a binwalk signature test script for
# a given input vector file. The test script will be written
# to the tests directory, and will expect the input vector file
# to be located in the tests/input-vectors/ directory.
import os
import sys
import binwalk

test_script_template = """
import os
import binwalk

def test_%s():
    '''
    Test: Open %s, scan for signatures
    verify that all (and only) expected signatures are detected
    '''
    expected_results = [
%s
    ]

    input_vector_file = os.path.join(os.path.dirname(__file__),
                                     "input-vectors",
                                     "%s")

    scan_result = binwalk.scan(input_vector_file,
                               signature=True,
                               quiet=True)

    # Test number of modules used
    assert len(scan_result) == 1

    # Test number of results for that module
    assert len(scan_result[0].results) == len(expected_results)

    # Test result-description
    for result, (expected_offset, expected_description) in zip(scan_result[0].results, expected_results):
        assert result.offset == expected_offset
        assert result.description == expected_description
"""

def main():
    try:
        target_file = sys.argv[1]
    except IndexError:
        sys.stderr.write("Usage: %s <input vector file>\n" % sys.argv[0])
        sys.exit(1)

    target_file_basename = os.path.basename(target_file)
    scan_function_name = target_file_basename.replace('.', '_').replace('-', '_')
    expected_results = ""

    signature = binwalk.scan(target_file, signature=True, term=True)[0]
    for result in signature.results:
        expected_results += "\t[%d, %r],\n" % (result.offset, result.description)

    test_script = test_script_template % (scan_function_name,
                                          target_file_basename,
                                          expected_results,
                                          target_file_basename)

    test_script_path = os.path.join("tests", "test_%s.py" % scan_function_name)

    with open(test_script_path, "w") as fp:
        fp.write(test_script)

    sys.stdout.write("Generated test script for '%s' and saved it to '%s'\n" % (target_file, test_script_path))


if __name__ == '__main__':
    main()
