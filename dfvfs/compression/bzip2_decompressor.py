"""The BZIP2 decompressor implementation."""

import bz2

from dfvfs.compression import decompressor
from dfvfs.compression import manager
from dfvfs.lib import definitions
from dfvfs.lib import errors


class BZIP2Decompressor(decompressor.Decompressor):
    """BZIP2 decompressor using bz2."""

    COMPRESSION_METHOD = definitions.COMPRESSION_METHOD_BZIP2

    _SIGNATURE = b"BZh"

    def __init__(self):
        """Initializes a decompressor."""
        super().__init__()
        self._bz2_decompressor = bz2.BZ2Decompressor()

    def Decompress(self, compressed_data):
        """Decompresses the compressed data.

        The compressed data can consist of multiple BZIP2 streams, such as
        created by pbzip2. A new stream is decompressed when the data after
        the end of the previous stream starts with the BZIP2 signature.

        Args:
          compressed_data (bytes): compressed data.

        Returns:
          tuple(bytes, bytes): uncompressed data and remaining compressed data.

        Raises:
          BackEndError: if the BZIP2 compressed stream cannot be decompressed.
        """
        uncompressed_data = []
        remaining_compressed_data = compressed_data

        try:
            while True:
                if self._bz2_decompressor.eof and remaining_compressed_data.startswith(
                    self._SIGNATURE
                ):
                    self._bz2_decompressor = bz2.BZ2Decompressor()

                uncompressed_data.append(
                    self._bz2_decompressor.decompress(remaining_compressed_data)
                )
                remaining_compressed_data = bytes(self._bz2_decompressor.unused_data)

                if not remaining_compressed_data.startswith(self._SIGNATURE):
                    break

        except (EOFError, OSError) as exception:
            raise errors.BackEndError(
                (
                    f"Unable to decompress BZIP2 compressed stream with error: "
                    f"{exception!s}."
                )
            )

        return b"".join(uncompressed_data), remaining_compressed_data


manager.CompressionManager.RegisterDecompressor(BZIP2Decompressor)
