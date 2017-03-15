from os.path import dirname

import binwalk
from nose.tools import eq_, ok_


def test_hello_world_simple_scan():
    '''
    Test: Open hello-world.ihex, scan for signatures
    verify that only one signature is returned
    verify that the only signature returned is Intel HEX data-signature
    '''
    scan_result = binwalk.scan(
        dirname(__file__) + '/input-vectors/hello-world.ihex',
        signature=True,
        quiet=True,
        extract=True)  # Throws a warning for missing external extractor
    # Test number of modules used
    eq_(len(scan_result), 1)
    # Test number of results for that module
    eq_(len(scan_result[0].results), 1)
    # Test result-description
    eq_(scan_result[0].results[0].description,
        'Intel HEX data, record type: data')
