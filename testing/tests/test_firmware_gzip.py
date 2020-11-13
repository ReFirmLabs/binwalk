
import os
import binwalk
from nose.tools import eq_, ok_

def test_firmware_gzip():
    '''
    Test: Open firmware.gzip, scan for signatures.
    Verify that only one gzip signature was detected.
    '''
    input_vector_file = os.path.join(os.path.dirname(__file__),
                                     "input-vectors",
                                     "firmware.gzip")

    scan_result = binwalk.scan(input_vector_file,
                               signature=True,
                               quiet=True)

    # Test number of modules used
    eq_(len(scan_result), 1)

    # There should be only one result
    eq_(len(scan_result[0].results), 1)

    # That result should be at offset 0
    eq_(scan_result[0].results[0].offset, 0)

    # That result should be a gzip file
    ok_(scan_result[0].results[0].description.startswith("gzip compressed data"))
