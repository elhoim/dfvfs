#!/usr/bin/env python3
"""Tests for the helper functions for Core Storage (CS) support."""

import unittest

import pyfvde

from dfvfs.credentials import keychain
from dfvfs.lib import cs_helper
from dfvfs.lib import definitions
from dfvfs.path import cs_path_spec
from dfvfs.path import factory as path_spec_factory
from dfvfs.path import fake_path_spec
from dfvfs.resolver import context
from dfvfs.resolver import resolver

from tests import test_lib as shared_test_lib


class TestFVDEVolume:
    """Fake Core Storage volume that records the calls made to it.

    Attributes:
      calls (list[tuple[str, object]]): names and arguments of the calls.
    """

    # pylint: disable=invalid-name

    def __init__(self):
        """Initializes a fake Core Storage volume."""
        super().__init__()
        self.calls = []

    def open_file_object(self, file_object):
        """Opens the volume using a file-like object.

        Args:
          file_object (FileIO): file-like object.
        """
        self.calls.append(("open_file_object", file_object))

    def read_encrypted_root_plist(self, path):
        """Reads the EncryptedRoot.plist.wipekey file.

        Args:
          path (str): path of the EncryptedRoot.plist.wipekey file.
        """
        self.calls.append(("read_encrypted_root_plist", path))


class CSHelperTest(shared_test_lib.BaseTestCase):
    """Tests for the helper functions for Core Storage (CS) support."""

    def testCSOpenVolume(self):
        """Tests the CSOpenVolume function."""
        test_fake_path_spec = fake_path_spec.FakePathSpec(location="/")
        path_spec = cs_path_spec.CSPathSpec(parent=test_fake_path_spec)

        test_file_object = object()
        test_key_chain = keychain.KeyChain()

        fvde_volume = TestFVDEVolume()
        cs_helper.CSOpenVolume(fvde_volume, path_spec, test_file_object, test_key_chain)
        self.assertEqual(fvde_volume.calls, [("open_file_object", test_file_object)])

        test_key_chain.SetCredential(
            path_spec, "encrypted_root_plist", "EncryptedRoot.plist.wipekey"
        )

        fvde_volume = TestFVDEVolume()
        cs_helper.CSOpenVolume(fvde_volume, path_spec, test_file_object, test_key_chain)
        self.assertEqual(
            fvde_volume.calls,
            [
                ("read_encrypted_root_plist", "EncryptedRoot.plist.wipekey"),
                ("open_file_object", test_file_object),
            ],
        )

    def testCSOpenVolumeOnCS(self):
        """Tests the CSOpenVolume function on a Core Storage image."""
        resolver_context = context.Context()

        test_path = self._GetTestFilePath(["fvdetest.qcow2"])
        self._SkipIfPathNotExists(test_path)

        test_os_path_spec = path_spec_factory.Factory.NewPathSpec(
            definitions.TYPE_INDICATOR_OS, location=test_path
        )
        test_qcow_path_spec = path_spec_factory.Factory.NewPathSpec(
            definitions.TYPE_INDICATOR_QCOW, parent=test_os_path_spec
        )
        test_gpt_path_spec = path_spec_factory.Factory.NewPathSpec(
            definitions.TYPE_INDICATOR_GPT, location="/p1", parent=test_qcow_path_spec
        )
        test_cs_path_spec = path_spec_factory.Factory.NewPathSpec(
            definitions.TYPE_INDICATOR_CS, parent=test_gpt_path_spec
        )

        file_object = resolver.Resolver.OpenFileObject(
            test_gpt_path_spec, resolver_context=resolver_context
        )

        fvde_volume = pyfvde.volume()
        try:
            cs_helper.CSOpenVolume(
                fvde_volume, test_cs_path_spec, file_object, keychain.KeyChain()
            )
            fvde_volume.open_physical_volume_files_as_file_objects([file_object])

            fvde_volume_group = fvde_volume.get_volume_group()
            self.assertEqual(fvde_volume_group.number_of_logical_volumes, 1)

        finally:
            fvde_volume.close()
            resolver_context.Empty()

    def testCSPathSpecGetVolumeIndex(self):
        """Tests the CSPathSpecGetVolumeIndex function."""
        test_fake_path_spec = fake_path_spec.FakePathSpec(location="/")

        path_spec = cs_path_spec.CSPathSpec(parent=test_fake_path_spec)

        self.assertIsNotNone(path_spec)

        volume_index = cs_helper.CSPathSpecGetVolumeIndex(path_spec)
        self.assertIsNone(volume_index)

        path_spec = cs_path_spec.CSPathSpec(location="/cs2", parent=test_fake_path_spec)

        self.assertIsNotNone(path_spec)

        volume_index = cs_helper.CSPathSpecGetVolumeIndex(path_spec)
        self.assertEqual(volume_index, 1)

        path_spec = cs_path_spec.CSPathSpec(volume_index=1, parent=test_fake_path_spec)

        self.assertIsNotNone(path_spec)

        volume_index = cs_helper.CSPathSpecGetVolumeIndex(path_spec)
        self.assertEqual(volume_index, 1)

        path_spec = cs_path_spec.CSPathSpec(
            location="/cs2", volume_index=1, parent=test_fake_path_spec
        )

        self.assertIsNotNone(path_spec)

        volume_index = cs_helper.CSPathSpecGetVolumeIndex(path_spec)
        self.assertEqual(volume_index, 1)

        path_spec = cs_path_spec.CSPathSpec(location="/cs", parent=test_fake_path_spec)

        volume_index = cs_helper.CSPathSpecGetVolumeIndex(path_spec)
        self.assertIsNone(volume_index)


if __name__ == "__main__":
    unittest.main()
