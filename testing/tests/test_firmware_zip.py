
import os
import binwalk
from nose.tools import eq_, ok_

def test_firmware_zip():
    '''
    Test: Open firmware.zip, scan for signatures
    verify that all (and only) expected signatures are detected
    '''
    expected_results = [
	[0, 'Zip archive data, at least v1.0 to extract, name: dir655_revB_FW_203NA/'],
	[6410581, 'End of Zip archive, footer length: 22'],

    ]

    input_vector_file = os.path.join(os.path.dirname(__file__),
                                     "input-vectors",
                                     "firmware.zip")

    scan_result = binwalk.scan(input_vector_file,
                               signature=True,
                               quiet=True)

    # Test number of modules used
    eq_(len(scan_result), 1)

    # Test number of results for that module
    eq_(len(scan_result[0].results), len(expected_results))

    # Test result-description
    for i in range(0, len(scan_result[0].results)):
        eq_(scan_result[0].results[i].offset, expected_results[i][0])
        eq_(scan_result[0].results[i].description, expected_results[i][1])
