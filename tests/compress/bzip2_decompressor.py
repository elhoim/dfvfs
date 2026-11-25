#!/usr/bin/env python3
"""Tests for the bzip2 decompressor object."""

import bz2
import unittest

from dfvfs.compression import bzip2_decompressor
from dfvfs.lib import errors

from tests.compress import test_lib


class BZIP2DecompressorTestCase(test_lib.DecompressorTestCase):
    """Tests for the bzip2 decompressor object."""

    def testDecompress(self):
        """Tests the Decompress method."""
        decompressor = bzip2_decompressor.BZIP2Decompressor()

        compressed_data = (
            b'BZh91AY&SYa\x0e\xf5A\x00\x00\x02\x13\x80@\x01\x04\x00"`\x0c\x00 '
            b'\x00!\xa3M\x19\x082b\x18Q#\xa5\xc1"\xf1w$S\x85\t\x06\x10\xefT\x10'
        )

        uncompressed_data, _ = decompressor.Decompress(compressed_data)
        expected_uncompressed_data = b"This is a test."
        self.assertEqual(uncompressed_data, expected_uncompressed_data)

        # Test to trigger bz2 raising EOFError.
        with self.assertRaises(errors.BackEndError):
            decompressor.Decompress(b"This is a test.")

        # Test to trigger bz2 raising OSError.
        decompressor = bzip2_decompressor.BZIP2Decompressor()

        with self.assertRaises(errors.BackEndError):
            decompressor.Decompress(b"This is a test.")

    def testDecompressMultipleStreams(self):
        """Tests the Decompress method with multiple streams."""
        compressed_data = b"".join(
            [bz2.compress(b"This is a test."), bz2.compress(b" And another one.")]
        )
        expected_uncompressed_data = b"This is a test. And another one."

        decompressor = bzip2_decompressor.BZIP2Decompressor()

        uncompressed_data, remaining_compressed_data = decompressor.Decompress(
            compressed_data
        )
        self.assertEqual(uncompressed_data, expected_uncompressed_data)
        self.assertEqual(remaining_compressed_data, b"")

        # Test with the compressed data split at every offset.
        for split_offset in range(1, len(compressed_data)):
            decompressor = bzip2_decompressor.BZIP2Decompressor()

            uncompressed_data, remaining_compressed_data = decompressor.Decompress(
                compressed_data[:split_offset]
            )
            remaining_compressed_data = b"".join(
                [remaining_compressed_data, compressed_data[split_offset:]]
            )
            uncompressed_data_part, remaining_compressed_data = decompressor.Decompress(
                remaining_compressed_data
            )
            uncompressed_data = b"".join([uncompressed_data, uncompressed_data_part])
            self.assertEqual(uncompressed_data, expected_uncompressed_data)
            self.assertEqual(remaining_compressed_data, b"")

        # Test with trailing data that is not a stream.
        decompressor = bzip2_decompressor.BZIP2Decompressor()

        uncompressed_data, remaining_compressed_data = decompressor.Decompress(
            b"".join([compressed_data, b"trailing"])
        )
        self.assertEqual(uncompressed_data, expected_uncompressed_data)
        self.assertEqual(remaining_compressed_data, b"trailing")


if __name__ == "__main__":
    unittest.main()
