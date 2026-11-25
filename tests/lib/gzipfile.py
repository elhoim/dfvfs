#!/usr/bin/env python3
"""Tests for gzip compressed stream file."""

# Note: do not rename file to gzip.py this can cause the exception:
# AttributeError: 'module' object has no attribute 'GzipFile'
# when using pip.

import gzip
import os
import unittest

from dfvfs.file_io import fake_file_io
from dfvfs.lib import definitions
from dfvfs.lib import errors
from dfvfs.lib import gzipfile
from dfvfs.path import factory as path_spec_factory
from dfvfs.path import fake_path_spec
from dfvfs.resolver import context
from dfvfs.resolver import resolver

from tests import test_lib as shared_test_lib

# TODO: add tests for _GzipDecompressorState
# TODO: add tests for GzipMember


class GzipCompressedStreamTest(shared_test_lib.BaseTestCase):
    """Tests a gzip compressed stream file-like object."""

    def _OpenFakeFileObject(self, resolver_context, file_data):
        """Opens a fake file-like object.

        Args:
          resolver_context (Context): resolver context.
          file_data (bytes): data of the fake file.

        Returns:
          FakeFile: fake file-like object.
        """
        path_spec = fake_path_spec.FakePathSpec(location="/test.gz")
        file_object = fake_file_io.FakeFile(resolver_context, path_spec, file_data)
        file_object.Open()
        return file_object

    def testOpenClose(self):
        """Test the Open and Close functions."""
        test_path = self._GetTestFilePath(["syslog.gz"])
        self._SkipIfPathNotExists(test_path)

        test_file = gzipfile.GzipCompressedStream()

        test_os_path_spec = path_spec_factory.Factory.NewPathSpec(
            definitions.TYPE_INDICATOR_OS, location=test_path
        )
        file_object = resolver.Resolver.OpenFileObject(test_os_path_spec)

        test_file.Open(file_object)

        try:
            self.assertEqual(len(test_file.members), 1)

        finally:
            test_file.close()

    def testSeek(self):
        """Test the seek functionality."""
        test_path = self._GetTestFilePath(["syslog.gz"])
        self._SkipIfPathNotExists(test_path)

        test_file = gzipfile.GzipCompressedStream()

        test_os_path_spec = path_spec_factory.Factory.NewPathSpec(
            definitions.TYPE_INDICATOR_OS, location=test_path
        )
        file_object = resolver.Resolver.OpenFileObject(test_os_path_spec)

        test_file.Open(file_object)

        try:
            test_file.seek(177)
            self.assertEqual(test_file.read(5), b"53:01")

            self.assertEqual(test_file.get_offset(), 182)

            test_file.seek(-10, os.SEEK_END)
            self.assertEqual(test_file.read(5), b"times")

            test_file.seek(2, os.SEEK_CUR)
            self.assertEqual(test_file.read(2), b"--")

            # Conforming to the POSIX seek the offset can exceed the file size
            # but reading will result in no data being returned.
            test_file.seek(2000, os.SEEK_SET)
            self.assertEqual(test_file.get_offset(), 2000)
            self.assertEqual(test_file.read(2), b"")

            # Test with an invalid offset.
            with self.assertRaises(OSError):
                test_file.seek(-10, os.SEEK_SET)

            # On error the offset should not change.
            self.assertEqual(test_file.get_offset(), 2000)

            # Test with an invalid whence.
            with self.assertRaises(OSError):
                test_file.seek(10, 5)

            # On error the offset should not change.
            self.assertEqual(test_file.get_offset(), 2000)

        finally:
            test_file.close()

    def testRead(self):
        """Test the read functionality."""
        test_path = self._GetTestFilePath(["syslog.gz"])
        self._SkipIfPathNotExists(test_path)

        test_file = gzipfile.GzipCompressedStream()

        test_os_path_spec = path_spec_factory.Factory.NewPathSpec(
            definitions.TYPE_INDICATOR_OS, location=test_path
        )
        file_object = resolver.Resolver.OpenFileObject(test_os_path_spec)

        test_file.Open(file_object)

        try:
            test_file.seek(167, os.SEEK_SET)

            self.assertEqual(test_file.get_offset(), 167)

            expected_data = (
                b"Jan 22 07:53:01 myhostname.myhost.com CRON[31051]: (root) CMD "
                b"(touch /var/run/crond.somecheck)\n"
            )

            data = test_file.read(95)
            self.assertEqual(data, expected_data)

            self.assertEqual(test_file.get_offset(), 262)

        finally:
            test_file.close()

    def testReadCorrupt(self):
        """Tests reading a file that is corrupt."""
        # The corrupt gzip has no member footer.
        test_path = self._GetTestFilePath(["corrupt1.gz"])
        self._SkipIfPathNotExists(test_path)

        test_file = gzipfile.GzipCompressedStream()

        test_os_path_spec = path_spec_factory.Factory.NewPathSpec(
            definitions.TYPE_INDICATOR_OS, location=test_path
        )
        file_object = resolver.Resolver.OpenFileObject(test_os_path_spec)

        test_file.Open(file_object)

        try:
            self.assertEqual(test_file.uncompressed_data_size, 2994187)

        finally:
            test_file.close()

    def testReadTrailingZeroPadding(self):
        """Tests reading a file with trailing 0-byte padding after the last member."""
        resolver_context = context.Context()

        for padding_size in (1, 16, 1024):
            file_data = b"".join(
                [
                    gzip.compress(b"hello"),
                    gzip.compress(b" world"),
                    b"\0" * padding_size,
                ]
            )
            file_object = self._OpenFakeFileObject(resolver_context, file_data)

            test_file = gzipfile.GzipCompressedStream()
            test_file.Open(file_object)

            try:
                self.assertEqual(len(test_file.members), 2)
                self.assertEqual(test_file.uncompressed_data_size, 11)
                self.assertEqual(test_file.read(11), b"hello world")

            finally:
                test_file.close()
                file_object.close()

    def testReadTrailingData(self):
        """Tests reading a file with trailing data that is not 0-byte padding."""
        resolver_context = context.Context()

        file_data = b"".join([gzip.compress(b"hello"), b"\0" * 16, b"garbage"])
        file_object = self._OpenFakeFileObject(resolver_context, file_data)

        test_file = gzipfile.GzipCompressedStream()

        try:
            with self.assertRaises(errors.FileFormatError):
                test_file.Open(file_object)

        finally:
            test_file.close()
            file_object.close()

    def testReadMultipleMembers(self):
        """Tests reading a file that contains multiple gzip members."""
        test_path = self._GetTestFilePath(["fsevents_000000000000b208"])
        self._SkipIfPathNotExists(test_path)

        test_file = gzipfile.GzipCompressedStream()

        test_os_path_spec = path_spec_factory.Factory.NewPathSpec(
            definitions.TYPE_INDICATOR_OS, location=test_path
        )
        file_object = resolver.Resolver.OpenFileObject(test_os_path_spec)

        test_file.Open(file_object)

        try:
            self.assertEqual(len(test_file.members), 2)

            file_start = test_file.read(4)
            self.assertEqual(file_start, b"1SLD")

            # Read the end of the second member
            test_file.seek(506631 - 4)
            file_end = test_file.read(4)
            self.assertEqual(file_end, b"\x02\x00\x80\x00")

            # Seek backwards, and read across a member boundary.
            test_file.seek(28530)
            self.assertEqual(test_file.read(6), b"OS\x00P\x07\x00")

            # Read with a size greater than the file size.
            test_file.seek(0)
            data = test_file.read(size=506631 + 4)
            self.assertEqual(len(data), 506631)
            self.assertEqual(data[-4:], b"\x02\x00\x80\x00")

        finally:
            test_file.close()


if __name__ == "__main__":
    unittest.main()
