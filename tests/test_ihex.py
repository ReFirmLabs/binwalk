import binwalk
from nose.tools import ok_, eq_
from os.path import dirname

def test_hello_world_simple_scan():
    scan_result = binwalk.scan(dirname(__file__)+'/input-vectors/hello-world.ihex', signature=True,quiet=True)
    ok_(scan_result != [])
    eq_(len(scan_result), 1)
    eq_(scan_result[0].results[0].description, 'Intel HEX data, record type: data')
