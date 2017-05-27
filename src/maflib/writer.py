"""A module for writing to a MAF file.

* MafWriter  a writer of a MAF file.
"""


import gzip

from maflib.logger import Logger
from maflib.validation import ValidationStringency
from maflib.record import MafRecord

class MafWriter(object):
    """A writer of a MAF file"""

    def __init__(self, handle, header, validation_stringency=None):
        self._handle = handle
        self._header = header
        self._logger = Logger.get_logger(self.__class__.__name__)

        self.validation_stringency = ValidationStringency.Silent \
            if (validation_stringency is None) else validation_stringency

        # validate the header
        self._header.validate(
            validation_stringency=self.validation_stringency,
            logger=self._logger
        )

        # write the header
        if len(self._header) > 0:
            self._handle.write(str(self._header) + "\n")

        scheme = self._header.scheme()
        if scheme:
            self._handle.write(
                MafRecord.ColumnSeparator.join(scheme.column_names()) + "\n"
            )
            self._written_column_names = True
        else:
            self._written_column_names = False

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

        # write the column names if not already written
        if not self._written_column_names:
            line = MafRecord.ColumnSeparator.join(
                str(key) for key in record.keys()
            )
            self._handle.write(line + "\n")
            self._written_column_names = True

        # write it
        self._handle.write(str(record) + "\n")
        return self

    def write(self, record):
        """Write a MafRecord. """
        return self.__iadd__(record)

    def close(self):
        """Closes the underlying file handle"""
        self._handle.close()

    @classmethod
    def writer_from(cls,
                    header,
                    validation_stringency=None,
                    path=None,
                    handle=None):
        """Create a MafWriter from the given path or file handle."""
        if not path:
            if not handle:
                raise Exception("Either a file path or file handle must be "
                                "given.")
        elif path.endswith(".gz"):
            handle = gzip.open(path, "wt")
        else:
            handle = open(path, "w")
        return MafWriter(
            handle=handle,
            header=header,
            validation_stringency=validation_stringency
        )