# Helpers

dfVFS currently provides the following helper objects:

* Data slice interface for file-like objects
* Fake file system builder
* Source scanner
* Volume scanner
* File system searcher
* Windows path resolver helper

## Data slice interface for file-like objects

The data slice interface for file-like objects provides a wrapper for dfVFS
FileIO objects, so that they can be interacted with as data slices. The data
slice interface is for example used in [Plaso's PE parser](https://github.com/log2timeline/plaso/blob/62d4fa7d25e793dba0557e12c5d61c6052a4a7a4/plaso/parsers/pe.py).

To create a data slice from a file-like object.

```python
from dfvfs.helpers import data_slice

...
slice_object = data_slice.DataSlice(file_object)
```

To use:

```python
signature = slice_object[0:4]
```

## Fake file system builder

The fake file system builder is intended for testing purposes. It provides
helper functions that take care of setting up a dfVFS fake file system.

To create a fake file system with a single file `/testfile`.

```python
from dfvfs.helpers import fake_file_system_builder

file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
file_system_builder.AddFile('/testfile', b'data')
```

## Source scanner

The source scanner was originally created for [Plaso](https://github.com/log2timeline/plaso/blob/993ab0111bbf594c9b6d679415c80f8409cad0b5/plaso/cli/storage_media_tool.py)
tools that deal with storage media devices and images. However it is also
used by the dfVFS volume scanner.

The source scanner can be used to analyze source (or input) data, which for
Plaso can be an individual file, a directory or a storage media device or
image.

The source scanner tries to determine what input we are dealing with:

* a file that contains a storage media image;
* a device file of a storage media image device;
* a regular file or directory.

The source scanner scans for different types of elements:

* supported types of storage media images;
* supported types of volume systems;
* supported types of file systems.

These elements are represented as source scan nodes.

The source scanner uses the source scanner context to keep track of
the nodes and user provided context information, such as:

* which partition to default to;
* which VSS stores to default to.

An example of how to use the source scanner can be found in the [source analyzer](https://github.com/open-source-dfir/dfvfs-snippets/blob/main/scripts/source_analyzer.py)
script.

## Volume scanner

The volume scanner is an extension of the source analyzer that looks for
volumes that contain dfVFS supported volume and file systems. It is intended
to help with programmatically handled various types of volume and file systems
so the application that uses it can focus on reading file it is interested in.

The volume scanner is configured with volume scanner options
(`VolumeScannerOptions`), that are passed to `GetBasePathSpecs`:

| **Option** | **Description** |
| --- | --- |
| `credentials` | List of (credential type, credential data) tuples, used to unlock encrypted volumes, for example `("password", "secret")` |
| `partitions` | Partition identifiers, for example `["p1"]` or `["all"]` |
| `scan_mode` | `SCAN_MODE_ALL` (default) to scan volumes and snapshots, `SCAN_MODE_SNAPSHOTS_ONLY` to scan only the snapshots of a volume system with snapshots, or `SCAN_MODE_VOLUMES_ONLY` to not scan snapshots |
| `snapshots` | Volume snapshot identifiers, for example `["vss1"]`, `["all"]` or `["none"]` |
| `volumes` | Volume identifiers, for example those of an APFS or LVM volume system, such as `["apfs1"]` or `["all"]` |

Identifiers can be specified with or without their prefix, for example `1` or
`p1`.

When the options do not determine which volumes to use, for example when
multiple partitions are found and no partitions are specified, the volume
scanner asks a volume scanner mediator (`VolumeScannerMediator`). An
application that uses the volume scanner can subclass the mediator to prompt
the user, by implementing:

* `GetAPFSVolumeIdentifiers`, to select APFS volumes;
* `GetLVMVolumeIdentifiers`, to select LVM volumes;
* `GetPartitionIdentifiers`, to select partitions;
* `GetVSSStoreIdentifiers`, to select Volume Shadow Snapshots (VSS);
* `UnlockEncryptedVolume`, to unlock an encrypted volume, for example by
  asking the user for a password.

Without a mediator the volume scanner raises a `ScannerError` when it cannot
determine how to proceed.

```python
from dfvfs.helpers import volume_scanner

options = volume_scanner.VolumeScannerOptions()
options.partitions = ["all"]
options.snapshots = ["none"]

scanner = volume_scanner.VolumeScanner()
base_path_specs = scanner.GetBasePathSpecs(source_path, options=options)
```

Examples of how to use the volume scanner can be found in the [list file entries](https://github.com/open-source-dfir/dfvfs-snippets/blob/main/scripts/list_file_entries.py)
and the [recursive hasher](https://github.com/open-source-dfir/dfvfs-snippets/blob/main/scripts/recursive_hasher.py)
scripts.

### Windows volume scanner

The Windows volume scanner is a variant of the volume scanner that looks for
volumes that contain an installation of the Windows operating system.

An example of how to use the source scanner can be found in the [WinReg-KB](https://github.com/libyal/winreg-kb/blob/2e285132b70ce036b7492921ad29f9caf663492e/winregrc/collector.py).

## File system searcher

The file system searcher was originally created for event extraction with
[collection filters](https://plaso.readthedocs.io/en/latest/sources/user/Collection-Filters.html)
in [Plaso](https://github.com/log2timeline/plaso/blob/993ab0111bbf594c9b6d679415c80f8409cad0b5/plaso/cli/storage_media_tool.py).

The file system searcher finds file entries in a file system that match
one or more find specifications (`FindSpec`). A find specification can
define:

* the location to match, as a plain location (`location`), a glob
  (`location_glob`) or a regular expression (`location_regex`), relative to
  the root of the file system. Only one of these can be used per find
  specification. A location can be provided as a string, which is split into
  segments using `location_separator`, or as a list of path segments;
* if the location should be matched case sensitive (`case_sensitive`);
* the file entry types to match (`file_entry_types`), for example
  `definitions.FILE_ENTRY_TYPE_FILE`;
* if the file entry should be allocated (`is_allocated`).

To find the files in `/Windows/System32/config`, case insensitive.

```python
from dfvfs.helpers import fake_file_system_builder
from dfvfs.helpers import file_system_searcher
from dfvfs.lib import definitions
from dfvfs.path import factory as path_spec_factory

file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
file_system_builder.AddFile("/Windows/System32/config/SAM", b"data")
file_system_builder.AddFile("/Windows/System32/config/SYSTEM", b"data")
file_system_builder.AddFile("/Windows/System32/drivers/etc/hosts", b"data")

mount_point = path_spec_factory.Factory.NewPathSpec(
    definitions.TYPE_INDICATOR_FAKE, location="/"
)
searcher = file_system_searcher.FileSystemSearcher(
    file_system_builder.file_system, mount_point
)

find_spec = file_system_searcher.FindSpec(
    case_sensitive=False,
    file_entry_types=[definitions.FILE_ENTRY_TYPE_FILE],
    location_glob="/windows/system32/config/*",
    location_separator="/",
)

for path_spec in searcher.Find(find_specs=[find_spec]):
    print(searcher.GetRelativePath(path_spec))
```

This prints:

```
/Windows/System32/config/SAM
/Windows/System32/config/SYSTEM
```

## Windows path resolver helper

The Windows path resolver helper can be used to resolve various forms Windows
paths, e.g. below are several forms of path definitions found in the Windows
Registry:

| **Description** | **Example** |
| --- | --- |
| Volume 'absolute' path | `C:\Windows\System32\icardres.dll` |
| Local 'absolute' path | `\Windows\System32\Drivers\acpiex.sys` |
| Local 'relative' path | `System32\Drivers\acpiex.sys` |
| Path with environment variable | `%systemroot%\system32\svchost.exe` |
| Short name volume 'absolute' path | `C:\PROGRA~1\COMMON~1\MICROS~1\DW\DW20.EXE` |
| | `\SystemRoot\System32\drivers\1394ohci.sys` |
| | `$(runtime.system32)\winhttp.dll` |
| | `\??\C:\WINDOWS\Microsoft.NET\Framework\v1.1.4322\ngen.exe` |
| | `SYSVOL\Windows\System32\wbem\WmiPrvSE.exe` |

The Windows path resolver helper can be found in:

```
dfvfs/helpers/windows_path_resolver.py
```

To resolve a Windows path in a file system, for example a fake file system
created with the fake file system builder.

```python
from dfvfs.helpers import windows_path_resolver

path_resolver = windows_path_resolver.WindowsPathResolver(
    file_system_builder.file_system, mount_point
)
path_resolver.SetEnvironmentVariable("SystemRoot", "C:\\Windows")

path_spec = path_resolver.ResolvePath("%SystemRoot%\\system32\\drivers\\etc\\HOSTS")
print(path_resolver.GetWindowsPath(path_spec))
```

This prints `C:\Windows\System32\drivers\etc\hosts`. Path segments are
matched case insensitive and the resolved path specification uses the names
as stored in the file system. `ResolvePath` returns None if the path cannot be
resolved.

### Notes

The table below lists forms of Windows paths and if `ResolvePath` supports
them. A drive letter of a volume 'absolute' path is not compared with the
drive letter of the resolver. `..` path segments cannot traverse above the
mount point.

| **Description** | **Example** | **Supported** |
| --- | --- | --- |
| Device path | `\\.\PhysicalDrive0` | No |
| Volume device path | `\\.\C:` | No |
| Volume file system path | `\\.\C:\` | Yes |
| Volume path | `\DEVICE\HARDDISKVOLUME2` | No |
| Extended-length path | `\\?\C:\directory\file.txt` | Yes |
| Extended-length UNC path | `\\?\UNC\server\share\directory\file.txt` | No |
| Local 'absolute' path | `\directory\file.txt` <br> `\directory\\file.txt` | Yes |
| Local 'relative' path | `directory\file.txt` <br> `..\directory\file.txt` <br> `.\directory\file.txt` | No |
| Volume 'absolute' path | `C:\directory\file.txt` | Yes |
| Volume 'relative' path | `C:directory\file.txt` | No |
| UNC path | `\\server\share\directory\file.txt` | No |
| Path with environment variable | `%SystemRoot%\file.txt` | Yes, if the environment variable is set |
| Path with trailing number to indicate the corresponding TYPELIB resource inside the PE/COFF | `C:\WINDOWS\PCHealth\HelpCtr\Binaries\HelpCtr.exe\1` | No |
| Path with volume creation time (FILETIME) and (volume) serial number (found in SuperFetch database and Prefetch files) | `\VOLUME{01d15f816d07b85e-5e6d77ca}\Windows\System32` | No |

