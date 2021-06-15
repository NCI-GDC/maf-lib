"""A module for writing to a MAF file.

* MafWriter  a writer of a MAF file.
"""


import gzip

from maflib.logger import Logger
from maflib.record import MafRecord
from maflib.schemes.no_restrictions_scheme import NoRestrictionsScheme
from maflib.sort_order import SortOrderChecker
from maflib.sorter import MafSorter
from maflib.validation import ValidationStringency


class MafWriter(object):
    """A writer of a MAF file"""

    def __init__(self, handle, header, validation_stringency=None, assume_sorted=True):
        self._handle = handle
        self._header = header
        self._logger = Logger.get_logger(self.__class__.__name__)
        self._assume_sorted = assume_sorted
        self._sorter = None
        self._checker = None

        self.validation_stringency = (
            ValidationStringency.Silent
            if (validation_stringency is None)
            else validation_stringency
        )

        # validate the header
        self._header.validate(
            validation_stringency=self.validation_stringency, logger=self._logger
        )

        # write the header
        if len(self._header) > 0:
            self._handle.write(str(self._header) + "\n")

        # write the column names if we have a scheme
        self._scheme = self._header.scheme()
        if self._scheme:
            self._handle.write(
                MafRecord.ColumnSeparator.join(self._scheme.column_names()) + "\n"
            )
            self._set_checker_and_sorter()

    def _set_checker_and_sorter(self):
        """Set the sort order checker and sorter.  Must be called **after**
        the scheme has been set."""
        if self._assume_sorted or not self._header.sort_order().sort_key():
            self._checker = SortOrderChecker(self._header.sort_order())
            self._sorter = None
        else:
            self._checker = None
            self._sorter = MafSorter(
                sort_order_name=self._header.sort_order().name(), scheme=self._scheme
            )

    def header(self):
        """Get the underlying MafHeader. """
        return self._header

    def __iadd__(self, record):
        """Write a MafRecord. """

        # set the scheme and write the column names if not already written
        if not self._scheme:
            column_names = [str(key) for key in record.keys()]
            self._scheme = NoRestrictionsScheme(column_names=column_names)
            self._handle.write(
                MafRecord.ColumnSeparator.join(self._scheme.column_names()) + "\n"
            )
            self._set_checker_and_sorter()

        # validate the record
        record.validate(
            validation_stringency=self.validation_stringency,
            logger=self._logger,
            reset_errors=True,
            scheme=self._scheme,
        )

        # either write it directly, or add it to the sorter
        if self._sorter:
            self._sorter += record
        else:
            self._handle.write(str(record) + "\n")

        return self

    def write(self, record):
        """Write a MafRecord. """
        return self.__iadd__(record)

    def close(self):
        """Closes the underlying file handle, and writes the records if the
        output was to be sorted."""
        if self._sorter:
            for rec in self._sorter:
                self._handle.write(str(rec) + "\n")
            self._sorter.close()
        self._handle.close()

    @classmethod
    def from_fd(cls, desc, header, validation_stringency=None, assume_sorted=True):
        """Create a MafWriter from the given file handle."""
        return MafWriter(
            handle=desc,
            header=header,
            validation_stringency=validation_stringency,
            assume_sorted=assume_sorted,
        )

    @classmethod
    def from_path(cls, path, header, validation_stringency=None, assume_sorted=True):
        """Create a MafWriter from the given path ."""
        if path.endswith(".gz"):
            handle = gzip.open(path, "wt")
        else:
            handle = open(path, "w")
        return MafWriter.from_fd(
            desc=handle,
            header=header,
            validation_stringency=validation_stringency,
            assume_sorted=assume_sorted,
        )
