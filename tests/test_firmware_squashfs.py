from os.path import dirname

import binwalk
from nose.tools import eq_, ok_


def test_firmware_squashfs():
    '''
    Test: Open hello-world.srec, scan for signatures
    verify that only one signature is returned
    verify that the only signature returned is Motorola S-rec data-signature
    '''
    expected_results = [
            [0, 'DLOB firmware header, boot partition: "dev=/dev/mtdblock/2"'],
            [112, 'LZMA compressed data, properties: 0x5D, dictionary size: 33554432 bytes, uncompressed size: 3466208 bytes'],
            [1179760, 'PackImg section delimiter tag, little endian size: 11548416 bytes; big endian size: 3649536 bytes'],
            [1179792, 'Squashfs filesystem, little endian, version 4.0, compression:lzma, size: 3647665 bytes, 1811 inodes, blocksize: 524288 bytes, created: 2013-09-17 06:43:22'],
            ]

    scan_result = binwalk.scan(
        dirname(__file__) + '/input-vectors/firmware.squashfs',
        signature=True,
        quiet=True,
        extract=True)  # Throws a warning for missing external extractor
    # Test number of modules used
    eq_(len(scan_result), 1)
    # Test number of results for that module
    eq_(len(scan_result[0].results), len(expected_results))
    # Test result-description
    for i in range(0, len(scan_result[0].results)):
        eq_(scan_result[0].results[i].offset, expected_results[i][0])
        eq_(scan_result[0].results[i].description, expected_results[i][1])
