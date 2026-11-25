#!/usr/bin/env python3
"""Script to generate the supported formats documentation."""

import argparse
import configparser
import os
import sys

# Change PYTHONPATH to include dfVFS.
sys.path.insert(0, ".")

# pylint: disable=wrong-import-position
import dfvfs

from dfvfs.analyzer import analyzer
from dfvfs.lib import definitions


class DataFormatDescriptor:
    """Descriptor of a supported data format.

    Attributes:
      name (str): name of the data format, for example "QCOW version 1, 2, 3".
      notes (list[str]): notes about the support of the data format.
      requirements (list[str]): names of the Python modules that provide
          support for the data format, where any of the modules is sufficient.
      type_indicators (list[str]): dfVFS type indicators that provide support
          for the data format.
    """

    def __init__(self, name, notes=None, requirements=None, type_indicators=None):
        """Initializes a data format descriptor.

        Args:
          name (str): name of the data format, for example "QCOW version 1, 2, 3".
          notes (Optional[list[str]]): notes about the support of the data format.
          requirements (Optional[list[str]]): names of the Python modules that
              provide support for the data format, where any of the modules is
              sufficient.
          type_indicators (Optional[list[str]]): dfVFS type indicators that
              provide support for the data format.
        """
        super().__init__()
        self.name = name
        self.notes = notes or []
        self.requirements = requirements or []
        self.type_indicators = type_indicators or []


class DataFormatCategory:
    """Category of supported data formats.

    Attributes:
      data_formats (list[DataFormatDescriptor]): data formats in the category.
      format_category (int): corresponding analyzer format category, as defined
          in definitions.FORMAT_CATEGORIES.
      title (str): title of the category, for example "Volume systems".
    """

    def __init__(self, title, format_category, data_formats):
        """Initializes a data format category.

        Args:
          title (str): title of the category, for example "Volume systems".
          format_category (int): corresponding analyzer format category, as
              defined in definitions.FORMAT_CATEGORIES.
          data_formats (list[DataFormatDescriptor]): data formats in the category.
        """
        super().__init__()
        self.data_formats = data_formats
        self.format_category = format_category
        self.title = title


class SupportedFormatsGenerator:
    """Generator of the supported formats documentation."""

    # Markdown links of the projects that provide the Python modules.
    _REQUIREMENTS = {
        "pybde": "[libbde/pybde](https://github.com/libyal/libbde)",
        "pycaes": "[libcaes/pycaes](https://github.com/libyal/libcaes)",
        "pyewf": "[libewf/pyewf](https://github.com/libyal/libewf)",
        "pyfcrypto": "[libfcrypto/pyfcrypto](https://github.com/libyal/libfcrypto)",
        "pyfsapfs": "[libfsapfs/pyfsapfs](https://github.com/libyal/libfsapfs)",
        "pyfsext": "[libfsext/pyfsext](https://github.com/libyal/libfsext)",
        "pyfsfat": "[libfsfat/pyfsfat](https://github.com/libyal/libfsfat)",
        "pyfshfs": "[libfshfs/pyfshfs](https://github.com/libyal/libfshfs)",
        "pyfsntfs": "[libfsntfs/pyfsntfs](https://github.com/libyal/libfsntfs)",
        "pyfsxfs": "[libfsxfs/pyfsxfs](https://github.com/libyal/libfsxfs)",
        "pyfvde": "[libfvde/pyfvde](https://github.com/libyal/libfvde)",
        "pyluksde": "[libluksde/pyluksde](https://github.com/libyal/libluksde)",
        "pymodi": "[libmodi/pymodi](https://github.com/libyal/libmodi)",
        "pyphdi": "[libphdi/pyphdi](https://github.com/libyal/libphdi)",
        "pyqcow": "[libqcow/pyqcow](https://github.com/libyal/libqcow)",
        "pysmdev": "[libsmdev/pysmdev](https://github.com/libyal/libsmdev)",
        "pysmraw": "[libsmraw/pysmraw](https://github.com/libyal/libsmraw)",
        "pytsk3": (
            "[libtsk](https://github.com/sleuthkit/sleuthkit/)/"
            "[pytsk](https://github.com/py4n6/pytsk)"
        ),
        "pyvhdi": "[libvhdi/pyvhdi](https://github.com/libyal/libvhdi)",
        "pyvmdk": "[libvmdk/pyvmdk](https://github.com/libyal/libvmdk)",
        "pyvsapm": "[libvsapm/pyvsapm](https://github.com/libyal/libvsapm)",
        "pyvsgpt": "[libvsgpt/pyvsgpt](https://github.com/libyal/libvsgpt)",
        "pyvshadow": "[libvshadow/pyvshadow](https://github.com/libyal/libvshadow)",
        "pyvslvm": "[libvslvm/pyvslvm](https://github.com/libyal/libvslvm)",
    }

    # Type indicators that do not represent a supported data format.
    _TYPE_INDICATORS_IGNORE_LIST = frozenset(
        [
            definitions.TYPE_INDICATOR_DATA_RANGE,
            definitions.TYPE_INDICATOR_FAKE,
            # TODO: add the data formats supported by Keramics.
            definitions.TYPE_INDICATOR_KERAMICS,
            definitions.TYPE_INDICATOR_MOUNT,
            definitions.TYPE_INDICATOR_OS,
        ]
    )

    _CATEGORIES = [
        DataFormatCategory(
            "Storage media types",
            definitions.FORMAT_CATEGORY_STORAGE_MEDIA_IMAGE,
            [
                DataFormatDescriptor(
                    "EWF (EWF-E01, EWF-Ex01, EWF-S01)",
                    requirements=["pyewf"],
                    type_indicators=[definitions.TYPE_INDICATOR_EWF],
                ),
                DataFormatDescriptor(
                    "Mac OS disk image",
                    notes=[
                        "Sparse bundle disk image",
                        "Sparse disk image",
                        "Universal Disk Image Format (UDIF) image",
                    ],
                    requirements=["pymodi"],
                    type_indicators=[definitions.TYPE_INDICATOR_MODI],
                ),
                DataFormatDescriptor(
                    "Parallels Hard Disk image format version 2",
                    requirements=["pyphdi"],
                    type_indicators=[definitions.TYPE_INDICATOR_PHDI],
                ),
                DataFormatDescriptor(
                    "QCOW version 1, 2, 3",
                    notes=["currently no differential image support"],
                    requirements=["pyqcow"],
                    type_indicators=[definitions.TYPE_INDICATOR_QCOW],
                ),
                DataFormatDescriptor("Storage Media device", requirements=["pysmdev"]),
                DataFormatDescriptor(
                    "(split) Storage Media RAW",
                    requirements=["pysmraw"],
                    type_indicators=[definitions.TYPE_INDICATOR_RAW],
                ),
                DataFormatDescriptor(
                    "VHD and VHDX",
                    requirements=["pyvhdi"],
                    type_indicators=[definitions.TYPE_INDICATOR_VHDI],
                ),
                DataFormatDescriptor(
                    "VMDK",
                    notes=["currently no differential image support"],
                    requirements=["pyvmdk"],
                    type_indicators=[definitions.TYPE_INDICATOR_VMDK],
                ),
            ],
        ),
        DataFormatCategory(
            "Volume systems",
            definitions.FORMAT_CATEGORY_VOLUME_SYSTEM,
            [
                DataFormatDescriptor(
                    "Apple Partition Map (APM)",
                    requirements=["pytsk3", "pyvsapm"],
                    type_indicators=[
                        definitions.TYPE_INDICATOR_APM,
                        definitions.TYPE_INDICATOR_TSK_PARTITION,
                    ],
                ),
                DataFormatDescriptor(
                    "Apple File System (APFS) container version 2",
                    requirements=["pyfsapfs"],
                    type_indicators=[definitions.TYPE_INDICATOR_APFS_CONTAINER],
                ),
                DataFormatDescriptor(
                    "BitLocker Disk Encryption (BDE)",
                    requirements=["pybde"],
                    type_indicators=[definitions.TYPE_INDICATOR_BDE],
                ),
                DataFormatDescriptor(
                    "BSD disklabel",
                    requirements=["pytsk3"],
                    type_indicators=[definitions.TYPE_INDICATOR_TSK_PARTITION],
                ),
                DataFormatDescriptor(
                    (
                        "Core Storage (CS) including FileVault Disk Encryption "
                        "(FVDE) (or FileVault 2)"
                    ),
                    requirements=["pyfvde"],
                    type_indicators=[definitions.TYPE_INDICATOR_CS],
                ),
                DataFormatDescriptor(
                    "GPT",
                    requirements=["pyvsgpt", "pytsk3"],
                    type_indicators=[
                        definitions.TYPE_INDICATOR_GPT,
                        definitions.TYPE_INDICATOR_TSK_PARTITION,
                    ],
                ),
                DataFormatDescriptor(
                    "LVM",
                    notes=["At the moment only single physical volume LVM support"],
                    requirements=["pyvslvm"],
                    type_indicators=[definitions.TYPE_INDICATOR_LVM],
                ),
                DataFormatDescriptor(
                    "Linux Unified Key Setup (LUKS)",
                    requirements=["pyluksde"],
                    type_indicators=[definitions.TYPE_INDICATOR_LUKSDE],
                ),
                DataFormatDescriptor(
                    "MBR",
                    requirements=["pytsk3"],
                    type_indicators=[definitions.TYPE_INDICATOR_TSK_PARTITION],
                ),
                DataFormatDescriptor(
                    "Volume Shadow Snapshots (VSS)",
                    requirements=["pyvshadow"],
                    type_indicators=[definitions.TYPE_INDICATOR_VSHADOW],
                ),
            ],
        ),
        DataFormatCategory(
            "File systems",
            definitions.FORMAT_CATEGORY_FILE_SYSTEM,
            [
                DataFormatDescriptor(
                    "Apple File System (APFS) version 2",
                    requirements=["pyfsapfs"],
                    type_indicators=[definitions.TYPE_INDICATOR_APFS],
                ),
                DataFormatDescriptor(
                    "ext version 2, 3, 4",
                    requirements=["pyfsext", "pytsk3"],
                    type_indicators=[
                        definitions.TYPE_INDICATOR_EXT,
                        definitions.TYPE_INDICATOR_TSK,
                    ],
                ),
                DataFormatDescriptor(
                    "FAT-12, FAT-16, FAT-32 and exFAT",
                    requirements=["pytsk3", "pyfsfat"],
                    type_indicators=[
                        definitions.TYPE_INDICATOR_FAT,
                        definitions.TYPE_INDICATOR_TSK,
                    ],
                ),
                DataFormatDescriptor(
                    "HFS+, HFSX",
                    requirements=["pyfshfs", "pytsk3"],
                    type_indicators=[
                        definitions.TYPE_INDICATOR_HFS,
                        definitions.TYPE_INDICATOR_TSK,
                    ],
                ),
                DataFormatDescriptor(
                    "ISO-9660 version 1",
                    requirements=["pytsk3"],
                    type_indicators=[definitions.TYPE_INDICATOR_TSK],
                ),
                DataFormatDescriptor(
                    "NTFS version 3",
                    requirements=["pyfsntfs", "pytsk3"],
                    type_indicators=[
                        definitions.TYPE_INDICATOR_NTFS,
                        definitions.TYPE_INDICATOR_TSK,
                    ],
                ),
                DataFormatDescriptor(
                    "UFS version 1, 2",
                    requirements=["pytsk3"],
                    type_indicators=[definitions.TYPE_INDICATOR_TSK],
                ),
                DataFormatDescriptor(
                    "XFS version 4, 5",
                    requirements=["pyfsxfs"],
                    type_indicators=[definitions.TYPE_INDICATOR_XFS],
                ),
            ],
        ),
        DataFormatCategory(
            "Compressed stream file types",
            definitions.FORMAT_CATEGORY_COMPRESSED_STREAM,
            [
                DataFormatDescriptor(
                    "bzip2",
                    type_indicators=[
                        definitions.TYPE_INDICATOR_BZIP2,
                        definitions.TYPE_INDICATOR_COMPRESSED_STREAM,
                    ],
                ),
                DataFormatDescriptor(
                    "gzip", type_indicators=[definitions.TYPE_INDICATOR_GZIP]
                ),
                DataFormatDescriptor(
                    "lzma",
                    type_indicators=[definitions.TYPE_INDICATOR_COMPRESSED_STREAM],
                ),
                DataFormatDescriptor(
                    "xz",
                    type_indicators=[
                        definitions.TYPE_INDICATOR_COMPRESSED_STREAM,
                        definitions.TYPE_INDICATOR_XZ,
                    ],
                ),
                DataFormatDescriptor(
                    "zlib (both zlib+DEFLATE and stand-alone DEFLATE)",
                    type_indicators=[definitions.TYPE_INDICATOR_COMPRESSED_STREAM],
                ),
            ],
        ),
        DataFormatCategory(
            "Encoded stream file types",
            definitions.FORMAT_CATEGORY_ENCODED_STREAM,
            [
                DataFormatDescriptor(
                    "base16",
                    type_indicators=[definitions.TYPE_INDICATOR_ENCODED_STREAM],
                ),
                DataFormatDescriptor(
                    "base32",
                    type_indicators=[definitions.TYPE_INDICATOR_ENCODED_STREAM],
                ),
                DataFormatDescriptor(
                    "base64",
                    type_indicators=[definitions.TYPE_INDICATOR_ENCODED_STREAM],
                ),
            ],
        ),
        DataFormatCategory(
            "Encrypted stream file types",
            definitions.FORMAT_CATEGORY_UNDEFINED,
            [
                DataFormatDescriptor(
                    "AES-CBC, AES-CFB, AES-ECB, AES-OFB",
                    requirements=["pycaes"],
                    type_indicators=[definitions.TYPE_INDICATOR_ENCRYPTED_STREAM],
                ),
                DataFormatDescriptor(
                    "Blowfish",
                    requirements=["pyfcrypto"],
                    type_indicators=[definitions.TYPE_INDICATOR_ENCRYPTED_STREAM],
                ),
                DataFormatDescriptor(
                    "DES3",
                    requirements=["pyfcrypto"],
                    type_indicators=[definitions.TYPE_INDICATOR_ENCRYPTED_STREAM],
                ),
                DataFormatDescriptor(
                    "RC4",
                    requirements=["pyfcrypto"],
                    type_indicators=[definitions.TYPE_INDICATOR_ENCRYPTED_STREAM],
                ),
            ],
        ),
        DataFormatCategory(
            "Archive file types",
            definitions.FORMAT_CATEGORY_ARCHIVE,
            [
                DataFormatDescriptor(
                    "cpio", type_indicators=[definitions.TYPE_INDICATOR_CPIO]
                ),
                DataFormatDescriptor(
                    "tar", type_indicators=[definitions.TYPE_INDICATOR_TAR]
                ),
                DataFormatDescriptor(
                    "zip", type_indicators=[definitions.TYPE_INDICATOR_ZIP]
                ),
            ],
        ),
        DataFormatCategory(
            "Other file types",
            definitions.FORMAT_CATEGORY_UNDEFINED,
            [
                DataFormatDescriptor(
                    "blob stored in SQlite",
                    type_indicators=[definitions.TYPE_INDICATOR_SQLITE_BLOB],
                ),
            ],
        ),
    ]

    def __init__(self, dependencies_file="dependencies.ini"):
        """Initializes a supported formats generator.

        Args:
          dependencies_file (Optional[str]): path of the dependencies.ini file.
        """
        super().__init__()
        self._dependencies_file = dependencies_file

    def _GetDependencyNames(self):
        """Retrieves the names of the dependencies.

        Returns:
          set[str]: names of the Python modules defined in dependencies.ini.
        """
        config_parser = configparser.ConfigParser(interpolation=None)
        with open(self._dependencies_file, encoding="utf-8") as file_object:
            config_parser.read_file(file_object)

        return set(config_parser.sections())

    def _GetTypeIndicators(self):
        """Retrieves the type indicators defined by dfVFS.

        Returns:
          set[str]: type indicators.
        """
        return {
            value
            for name, value in vars(definitions).items()
            if name.startswith("TYPE_INDICATOR_")
        }

    def CheckDescriptors(self):
        """Checks the data format descriptors against dfVFS.

        Returns:
          list[str]: descriptions of the issues found, if any.
        """
        issues = []

        # Importing dfvfs.analyzer registers the analyzer helpers.
        # pylint: disable=protected-access
        analyzer_helpers = analyzer.Analyzer._analyzer_helpers
        # pylint: enable=protected-access
        dependency_names = self._GetDependencyNames()
        type_indicators = self._GetTypeIndicators()

        described_type_indicators = set()
        for category in self._CATEGORIES:
            for data_format in category.data_formats:
                for requirement in data_format.requirements:
                    if requirement not in dependency_names:
                        issues.append(
                            f"{data_format.name:s}: requirement: {requirement:s} "
                            f"not defined in: {self._dependencies_file:s}"
                        )
                    if requirement not in self._REQUIREMENTS:
                        issues.append(
                            f"{data_format.name:s}: requirement: {requirement:s} "
                            f"missing project link"
                        )

                for type_indicator in data_format.type_indicators:
                    if type_indicator not in type_indicators:
                        issues.append(
                            f"{data_format.name:s}: unsupported type indicator: "
                            f"{type_indicator:s}"
                        )
                        continue

                    described_type_indicators.add(type_indicator)

                    analyzer_helper = analyzer_helpers.get(type_indicator, None)
                    if (
                        analyzer_helper
                        and category.format_category
                        not in analyzer_helper.format_categories
                    ):
                        issues.append(
                            f"{data_format.name:s}: type indicator: "
                            f"{type_indicator:s} not in analyzer format category "
                            f"of: {category.title:s}"
                        )

        for type_indicator in sorted(
            type_indicators - self._TYPE_INDICATORS_IGNORE_LIST
        ):
            if type_indicator not in described_type_indicators:
                issues.append(f"type indicator: {type_indicator:s} not described")

        for type_indicator in sorted(analyzer_helpers.keys()):
            if type_indicator not in described_type_indicators:
                issues.append(
                    f"analyzer helper type indicator: {type_indicator:s} not described"
                )

        return issues

    def FormatSupportedFormats(self):
        """Formats the supported formats documentation.

        Returns:
          str: supported formats documentation in Markdown.
        """
        lines = [
            "## Supported Formats",
            "",
            f"The information below is based of version {dfvfs.__version__:s}",
            "",
        ]
        for category in self._CATEGORIES:
            lines.extend([f"### {category.title:s}", ""])

            for data_format in category.data_formats:
                line = f"* {data_format.name:s}"
                if data_format.requirements:
                    requirements = " or ".join(
                        [
                            self._REQUIREMENTS[requirement]
                            for requirement in data_format.requirements
                        ]
                    )
                    line = f"{line:s} (Requires: {requirements:s})"

                lines.append(line)
                lines.extend([f"  * {note:s}" for note in data_format.notes])

            lines.append("")

        return "\n".join(lines)


def Main():
    """The main program function.

    Returns:
      int: exit code that is provided to sys.exit().
    """
    argument_parser = argparse.ArgumentParser(
        description=(
            "Generates the supported formats documentation "
            "(docs/sources/Supported-formats.md)."
        )
    )

    argument_parser.add_argument(
        "--dependencies",
        dest="dependencies_file",
        action="store",
        metavar="PATH",
        default=os.path.join(".", "dependencies.ini"),
        help="path of the dependencies.ini file.",
    )

    options = argument_parser.parse_args()

    generator = SupportedFormatsGenerator(dependencies_file=options.dependencies_file)

    issues = generator.CheckDescriptors()
    if issues:
        for issue in issues:
            print(f"ERROR: {issue:s}", file=sys.stderr)
        return 1

    print(generator.FormatSupportedFormats(), end="")

    return 0


if __name__ == "__main__":
    sys.exit(Main())
