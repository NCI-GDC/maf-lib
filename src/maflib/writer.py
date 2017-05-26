"""A module for writing to a MAF file.

* MafWriter  a writer of a MAF file.
"""


import gzip

from maflib.logger import Logger
from maflib.validation import ValidationStringency


class MafWriter(object):
    """A writer of a MAF file"""

    def __init__(self, path, header, validation_stringency=None):
        self._path = path
        self._header = header
        self._logger = Logger.get_logger(self.__class__.__name__)

        self.validation_stringency = ValidationStringency.Silent \
            if (validation_stringency is None) else validation_stringency

        if path.endswith(".gz"):
            self._handle = gzip.open(path, "wt")
        else:
            self._handle = open(path, "w")

        # validate the header
        self._header.validate(
            validation_stringency=self.validation_stringency,
            logger=self._logger
        )

        # write the header
        if len(self._header) > 0:
            self._handle.write(str(self._header) + "\n")

    def header(self):
        """Get the underlying MafHeader. """
        return self._header

    def __iadd__(self, record):
        """Write a MafRecord. """

        # validate the record
        scheme = self._header.scheme()
        record.validate(
            validation_stringency=self.validation_stringency,
            logger=self._logger,
            reset_errors=True,
            scheme=scheme
        )

        # write it
        self._handle.write(str(record) + "\n")
        return self

    def write(self, record):
        """Write a MafRecord. """
        return self.__iadd__(record)

    def close(self):
        """Closes the underlying file handle"""
        self._handle.close()
