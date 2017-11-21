
import os
import binwalk
from nose.tools import eq_, ok_

def test_lzma():
    '''
    Test: Open foobar.lzma, scan for signatures.
    Verify that only one LZMA signature was detected.
    '''
    expected_result = "LZMA compressed data, properties: 0x5D, dictionary size: 8388608 bytes, uncompressed size: -1 bytes"

    input_vector_file = os.path.join(os.path.dirname(__file__),
                                     "input-vectors",
                                     "foobar.lzma")

    scan_result = binwalk.scan(input_vector_file,
                               signature=True,
                               quiet=True)

    # Test number of modules used
    eq_(len(scan_result), 1)

    # There should be only one result
    eq_(len(scan_result[0].results), 1)

    # That result should be at offset 0
    eq_(scan_result[0].results[0].offset, 0)

    # That result should be an LZMA file
    ok_(scan_result[0].results[0].description == expected_result)
