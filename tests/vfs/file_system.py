#!/usr/bin/env python3
"""Tests for the VFS file system object interface."""

import unittest

from dfvfs.path import fake_path_spec
from dfvfs.resolver import context
from dfvfs.vfs import file_system

from tests import test_lib as shared_test_lib


class TestFileSystem(file_system.FileSystem):
    """File system for testing."""

    # pylint: disable=abstract-method

    TYPE_INDICATOR = "test"


class FileSystemTest(shared_test_lib.BaseTestCase):
    """Tests the VFS file system object interface."""

    def setUp(self):
        """Sets up the needed objects used throughout the test."""
        self._resolver_context = context.Context()

    def testInitialize(self):
        """Test the __init__ function."""
        path_spec = fake_path_spec.FakePathSpec(location="/")

        with self.assertRaises(ValueError):
            file_system.FileSystem(self._resolver_context, path_spec)

    # TODO: add tests for type_indicator property.
    # TODO: add tests for _Close function.
    # TODO: add tests for _Open function.
    # TODO: add tests for BasenamePath function.
    # TODO: add tests for Close function.
    # TODO: add tests for DirnamePath function.
    # TODO: add tests for GetDataStreamByPathSpec function.
    # TODO: add tests for GetFileObjectByPathSpec function.
    # TODO: add tests for GetPathSegmentAndSuffix function.

    def testJoinPath(self):
        """Test the join path functionality."""
        path_spec = fake_path_spec.FakePathSpec(location="/")

        test_file_system = TestFileSystem(self._resolver_context, path_spec)

        expected_path = "/test1/test2/test3"

        path = test_file_system.JoinPath(["test1", "test2", "test3"])
        self.assertEqual(path, expected_path)

        path = test_file_system.JoinPath(["/test1", "test2//", "test3/"])
        self.assertEqual(path, expected_path)

        path = test_file_system.JoinPath(["/test1/test2/", "/test3/"])
        self.assertEqual(path, expected_path)

        path = test_file_system.JoinPath(["/test1///test2", "test3"])
        self.assertEqual(path, expected_path)

    def testJoinPathWithSpecialPathSegments(self):
        """Test the join path functionality with special path segments."""
        path_spec = fake_path_spec.FakePathSpec(location="/")

        test_file_system = TestFileSystem(self._resolver_context, path_spec)

        # None and empty path segments are ignored.
        path = test_file_system.JoinPath([None, "test1", None, "test2", None])
        self.assertEqual(path, "/test1/test2")

        path = test_file_system.JoinPath(["", "test1", "", "test2", ""])
        self.assertEqual(path, "/test1/test2")

        path = test_file_system.JoinPath([None])
        self.assertEqual(path, "/")

        path = test_file_system.JoinPath([""])
        self.assertEqual(path, "/")

        path = test_file_system.JoinPath([])
        self.assertEqual(path, "/")

        # "." and ".." path segments are preserved since storage media and
        # archive formats can contain them as literal names.
        path = test_file_system.JoinPath([".", "test1", ".", "test2", "."])
        self.assertEqual(path, "/./test1/./test2/.")

        path = test_file_system.JoinPath(["..", "test1", "..", "test2", ".."])
        self.assertEqual(path, "/../test1/../test2/..")

    # TODO: add tests for Open function.

    def testSplitPath(self):
        """Test the split path functionality."""
        path_spec = fake_path_spec.FakePathSpec(location="/")

        test_file_system = TestFileSystem(self._resolver_context, path_spec)

        expected_path_segments = ["test1", "test2", "test3"]

        path_segments = test_file_system.SplitPath("/test1/test2/test3")
        self.assertEqual(path_segments, expected_path_segments)

        path_segments = test_file_system.SplitPath("/test1/test2/test3/")
        self.assertEqual(path_segments, expected_path_segments)

        path_segments = test_file_system.SplitPath("/test1///test2/test3")
        self.assertEqual(path_segments, expected_path_segments)


if __name__ == "__main__":
    unittest.main()
