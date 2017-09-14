
import binwalk
from os.path import dirname
from nose.tools import eq_, ok_

def test_firmware_gzip():
    '''
    Test: Open firmware.gzip, scan for signatures
    verify that all (and only) expected signatures are detected
    '''
    expected_results = [
	[0, 'uImage header, header size: 64 bytes, header CRC: 0x29953343, created: 2011-06-27 07:33:02, image size: 6395843 bytes, Data Address: 0x40100000, Entry Point: 0x408A6270, data CRC: 0x3D73C1BC, OS: Linux, image type: OS Kernel Image, compression type: gzip, image name: "Unknown - IP7160_DIR855_F_Board"'],
	[64, 'gzip compressed data, maximum compression, from Unix, last modified: 2011-06-27 07:33:00'],

    ]

    scan_result = binwalk.scan(dirname(__file__) + '/input-vectors/firmware.gzip',
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
