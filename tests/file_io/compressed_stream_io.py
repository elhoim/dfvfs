#!/usr/bin/env python3
"""Tests for the compressed stream file-like object."""

import os
import unittest
import zlib

from dfvfs.file_io import compressed_stream_io
from dfvfs.file_io import fake_file_io
from dfvfs.lib import definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.path import fake_path_spec
from dfvfs.resolver import context

from tests.file_io import test_lib


class BZIP2CompressedStreamTest(test_lib.SyslogTestCase):
    """The unit test for a BZIP2 compressed stream file-like object."""

    def setUp(self):
        """Sets up the needed objects used throughout the test."""
        self._resolver_context = context.Context()
        test_path = self._GetTestFilePath(["syslog.bz2"])
        self._SkipIfPathNotExists(test_path)

        test_os_path_spec = path_spec_factory.Factory.NewPathSpec(
            definitions.TYPE_INDICATOR_OS, location=test_path
        )
        self._compressed_stream_path_spec = path_spec_factory.Factory.NewPathSpec(
            definitions.TYPE_INDICATOR_COMPRESSED_STREAM,
            compression_method=definitions.COMPRESSION_METHOD_BZIP2,
            parent=test_os_path_spec,
        )

    def tearDown(self):
        """Cleans up the needed objects used throughout the test."""
        self._resolver_context.Empty()

    def testOpenCloseFileObject(self):
        """Test the open and close functionality using a file-like object."""
        file_object = compressed_stream_io.CompressedStream(
            self._resolver_context, self._compressed_stream_path_spec
        )
        file_object.Open()

        self._TestGetSizeFileObject(file_object)

    def testOpenClosePathSpec(self):
        """Test the open and close functionality using a path specification."""
        file_object = compressed_stream_io.CompressedStream(
            self._resolver_context, self._compressed_stream_path_spec
        )
        file_object.Open()

        self._TestGetSizeFileObject(file_object)

    def testSeek(self):
        """Test the seek functionality."""
        file_object = compressed_stream_io.CompressedStream(
            self._resolver_context, self._compressed_stream_path_spec
        )
        file_object.Open()

        self._TestSeekFileObject(file_object)

        # Test SEEK_CUR after open.
        file_object = compressed_stream_io.CompressedStream(
            self._resolver_context, self._compressed_stream_path_spec
        )
        file_object.Open()

        file_object.seek(177, os.SEEK_CUR)
        self.assertEqual(file_object.read(5), b"53:01")

        # Test SEEK_END after open.
        file_object = compressed_stream_io.CompressedStream(
            self._resolver_context, self._compressed_stream_path_spec
        )
        file_object.Open()

        file_object.seek(-10, os.SEEK_END)
        self.assertEqual(file_object.read(5), b"times")

    def testRead(self):
        """Test the read functionality."""
        file_object = compressed_stream_io.CompressedStream(
            self._resolver_context, self._compressed_stream_path_spec
        )
        file_object.Open()

        self._TestReadFileObject(file_object)


class DeflateCompressedStreamTest(test_lib.SyslogTestCase):
    """The unit test for a DEFLATE compressed stream file-like object."""

    def setUp(self):
        """Sets up the needed objects used throughout the test."""
        self._resolver_context = context.Context()
        test_path = self._GetTestFilePath(["syslog"])
        self._SkipIfPathNotExists(test_path)

        with open(test_path, "rb") as file_object:
            uncompressed_data = file_object.read()

        # Raw DEFLATE compressed data without a zlib header and footer.
        compressor = zlib.compressobj(wbits=-zlib.MAX_WBITS)
        compressed_data = b"".join(
            [compressor.compress(uncompressed_data), compressor.flush()]
        )

        test_fake_path_spec = fake_path_spec.FakePathSpec(location="/syslog.deflate")
        self._fake_file_object = fake_file_io.FakeFile(
            self._resolver_context, test_fake_path_spec, compressed_data
        )
        self._fake_file_object.Open()
        self._resolver_context.CacheFileObject(
            test_fake_path_spec, self._fake_file_object
        )

        self._compressed_stream_path_spec = path_spec_factory.Factory.NewPathSpec(
            definitions.TYPE_INDICATOR_COMPRESSED_STREAM,
            compression_method=definitions.COMPRESSION_METHOD_DEFLATE,
            parent=test_fake_path_spec,
        )

    def tearDown(self):
        """Cleans up the needed objects used throughout the test."""
        self._fake_file_object.close()
        self._resolver_context.Empty()

    def testOpenCloseFileObject(self):
        """Test the open and close functionality using a file-like object."""
        file_object = compressed_stream_io.CompressedStream(
            self._resolver_context, self._compressed_stream_path_spec
        )
        file_object.Open()

        self._TestGetSizeFileObject(file_object)

    def testOpenClosePathSpec(self):
        """Test the open and close functionality using a path specification."""
        file_object = compressed_stream_io.CompressedStream(
            self._resolver_context, self._compressed_stream_path_spec
        )
        file_object.Open()

        self._TestGetSizeFileObject(file_object)

    def testSeek(self):
        """Test the seek functionality."""
        file_object = compressed_stream_io.CompressedStream(
            self._resolver_context, self._compressed_stream_path_spec
        )
        file_object.Open()

        self._TestSeekFileObject(file_object)

        # Test SEEK_CUR after open.
        file_object = compressed_stream_io.CompressedStream(
            self._resolver_context, self._compressed_stream_path_spec
        )
        file_object.Open()

        file_object.seek(177, os.SEEK_CUR)
        self.assertEqual(file_object.read(5), b"53:01")

        # Test SEEK_END after open.
        file_object = compressed_stream_io.CompressedStream(
            self._resolver_context, self._compressed_stream_path_spec
        )
        file_object.Open()

        file_object.seek(-10, os.SEEK_END)
        self.assertEqual(file_object.read(5), b"times")

    def testRead(self):
        """Test the read functionality."""
        file_object = compressed_stream_io.CompressedStream(
            self._resolver_context, self._compressed_stream_path_spec
        )
        file_object.Open()

        self._TestReadFileObject(file_object)


class LZMACompressedStreamTest(test_lib.SyslogTestCase):
    """The unit test for a LZMA compressed stream file-like object."""

    def setUp(self):
        """Sets up the needed objects used throughout the test."""
        self._resolver_context = context.Context()
        test_path = self._GetTestFilePath(["syslog.lzma"])
        self._SkipIfPathNotExists(test_path)

        test_os_path_spec = path_spec_factory.Factory.NewPathSpec(
            definitions.TYPE_INDICATOR_OS, location=test_path
        )
        self._compressed_stream_path_spec = path_spec_factory.Factory.NewPathSpec(
            definitions.TYPE_INDICATOR_COMPRESSED_STREAM,
            compression_method=definitions.COMPRESSION_METHOD_LZMA,
            parent=test_os_path_spec,
        )

    def tearDown(self):
        """Cleans up the needed objects used throughout the test."""
        self._resolver_context.Empty()

    def testOpenCloseFileObject(self):
        """Test the open and close functionality using a file-like object."""
        file_object = compressed_stream_io.CompressedStream(
            self._resolver_context, self._compressed_stream_path_spec
        )
        file_object.Open()

        self._TestGetSizeFileObject(file_object)

    def testOpenClosePathSpec(self):
        """Test the open and close functionality using a path specification."""
        file_object = compressed_stream_io.CompressedStream(
            self._resolver_context, self._compressed_stream_path_spec
        )
        file_object.Open()

        self._TestGetSizeFileObject(file_object)

    def testSeek(self):
        """Test the seek functionality."""
        file_object = compressed_stream_io.CompressedStream(
            self._resolver_context, self._compressed_stream_path_spec
        )
        file_object.Open()

        self._TestSeekFileObject(file_object)

        # Test SEEK_CUR after open.
        file_object = compressed_stream_io.CompressedStream(
            self._resolver_context, self._compressed_stream_path_spec
        )
        file_object.Open()

        file_object.seek(177, os.SEEK_CUR)
        self.assertEqual(file_object.read(5), b"53:01")

        # Test SEEK_END after open.
        file_object = compressed_stream_io.CompressedStream(
            self._resolver_context, self._compressed_stream_path_spec
        )
        file_object.Open()

        file_object.seek(-10, os.SEEK_END)
        self.assertEqual(file_object.read(5), b"times")

    def testRead(self):
        """Test the read functionality."""
        file_object = compressed_stream_io.CompressedStream(
            self._resolver_context, self._compressed_stream_path_spec
        )
        file_object.Open()

        self._TestReadFileObject(file_object)


class XZCompressedStreamTest(test_lib.SyslogTestCase):
    """The unit test for a XZ compressed stream file-like object."""

    def setUp(self):
        """Sets up the needed objects used throughout the test."""
        self._resolver_context = context.Context()
        test_path = self._GetTestFilePath(["syslog.xz"])
        self._SkipIfPathNotExists(test_path)

        test_os_path_spec = path_spec_factory.Factory.NewPathSpec(
            definitions.TYPE_INDICATOR_OS, location=test_path
        )
        self._compressed_stream_path_spec = path_spec_factory.Factory.NewPathSpec(
            definitions.TYPE_INDICATOR_COMPRESSED_STREAM,
            compression_method=definitions.COMPRESSION_METHOD_XZ,
            parent=test_os_path_spec,
        )

    def tearDown(self):
        """Cleans up the needed objects used throughout the test."""
        self._resolver_context.Empty()

    def testOpenCloseFileObject(self):
        """Test the open and close functionality using a file-like object."""
        file_object = compressed_stream_io.CompressedStream(
            self._resolver_context, self._compressed_stream_path_spec
        )
        file_object.Open()

        self._TestGetSizeFileObject(file_object)

    def testOpenClosePathSpec(self):
        """Test the open and close functionality using a path specification."""
        file_object = compressed_stream_io.CompressedStream(
            self._resolver_context, self._compressed_stream_path_spec
        )
        file_object.Open()

        self._TestGetSizeFileObject(file_object)

    def testSeek(self):
        """Test the seek functionality."""
        file_object = compressed_stream_io.CompressedStream(
            self._resolver_context, self._compressed_stream_path_spec
        )
        file_object.Open()

        self._TestSeekFileObject(file_object)

        # Test SEEK_CUR after open.
        file_object = compressed_stream_io.CompressedStream(
            self._resolver_context, self._compressed_stream_path_spec
        )
        file_object.Open()

        file_object.seek(177, os.SEEK_CUR)
        self.assertEqual(file_object.read(5), b"53:01")

        # Test SEEK_END after open.
        file_object = compressed_stream_io.CompressedStream(
            self._resolver_context, self._compressed_stream_path_spec
        )
        file_object.Open()

        file_object.seek(-10, os.SEEK_END)
        self.assertEqual(file_object.read(5), b"times")

    def testRead(self):
        """Test the read functionality."""
        file_object = compressed_stream_io.CompressedStream(
            self._resolver_context, self._compressed_stream_path_spec
        )
        file_object.Open()

        self._TestReadFileObject(file_object)


class ZlibCompressedStreamTest(test_lib.SyslogTestCase):
    """The unit test for a zlib compressed stream file-like object."""

    def setUp(self):
        """Sets up the needed objects used throughout the test."""
        self._resolver_context = context.Context()
        test_path = self._GetTestFilePath(["syslog.zlib"])
        self._SkipIfPathNotExists(test_path)

        test_os_path_spec = path_spec_factory.Factory.NewPathSpec(
            definitions.TYPE_INDICATOR_OS, location=test_path
        )
        self._compressed_stream_path_spec = path_spec_factory.Factory.NewPathSpec(
            definitions.TYPE_INDICATOR_COMPRESSED_STREAM,
            compression_method=definitions.COMPRESSION_METHOD_ZLIB,
            parent=test_os_path_spec,
        )

    def tearDown(self):
        """Cleans up the needed objects used throughout the test."""
        self._resolver_context.Empty()

    def testOpenCloseFileObject(self):
        """Test the open and close functionality using a file-like object."""
        file_object = compressed_stream_io.CompressedStream(
            self._resolver_context, self._compressed_stream_path_spec
        )
        file_object.Open()

        self._TestGetSizeFileObject(file_object)

    def testOpenClosePathSpec(self):
        """Test the open and close functionality using a path specification."""
        file_object = compressed_stream_io.CompressedStream(
            self._resolver_context, self._compressed_stream_path_spec
        )
        file_object.Open()

        self._TestGetSizeFileObject(file_object)

    def testSeek(self):
        """Test the seek functionality."""
        file_object = compressed_stream_io.CompressedStream(
            self._resolver_context, self._compressed_stream_path_spec
        )
        file_object.Open()

        self._TestSeekFileObject(file_object)

        # Test SEEK_CUR after open.
        file_object = compressed_stream_io.CompressedStream(
            self._resolver_context, self._compressed_stream_path_spec
        )
        file_object.Open()

        file_object.seek(177, os.SEEK_CUR)
        self.assertEqual(file_object.read(5), b"53:01")

        # Test SEEK_END after open.
        file_object = compressed_stream_io.CompressedStream(
            self._resolver_context, self._compressed_stream_path_spec
        )
        file_object.Open()

        file_object.seek(-10, os.SEEK_END)
        self.assertEqual(file_object.read(5), b"times")

    def testRead(self):
        """Test the read functionality."""
        file_object = compressed_stream_io.CompressedStream(
            self._resolver_context, self._compressed_stream_path_spec
        )
        file_object.Open()

        self._TestReadFileObject(file_object)


if __name__ == "__main__":
    unittest.main()
