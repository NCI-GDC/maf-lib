"""A module for reading from a MAF file.

* MafReader  a reader for a MAF file.
"""

import gzip

from maflib.header import MafHeader
from maflib.logger import Logger
from maflib.record import MafRecord
from maflib.schemes import NoRestrictionsScheme
from maflib.validation import ValidationStringency, MafValidationError, \
    MafValidationErrorType


class MafReader(object):
    """A reader for a MAF file.

    The reader initially reads in the header and column definitions from the MAF
    file.  The reader can then be used to iterate through the MAF records (
    lines) one-by-one.
    """

    def __init__(self, lines,
                 closeable=None,
                 validation_stringency=None,
                 scheme=None):
        """ Initializes a MAF reader and reads in the header and column
        definitions.

        If no scheme is provided, the scheme will be determined from the
        version and annotation pragmas in the header, and matched against the
        known set of schemes.  If the scheme is not recognized, then the
        column names will determine a custom scheme and no assumption is made
        about the values of each column.

        :param lines: the lines (iterable) from the MAF file.
        :param closeable: any closeable object (has a ``close()`` method) that
        will be closed when ``close()`` is called.
        :param validation_stringency: the validation stringency.
        :param scheme: a scheme that should be used to override the scheme in
        the header.
        """
        self.__iter = iter(lines)
        self.__closeable = closeable
        self.validation_stringency = \
            ValidationStringency.Silent if (validation_stringency is None) \
                else validation_stringency
        self.__logger = Logger.get_logger(self.__class__.__name__)
        self.validation_errors = list()

        self.__next_line = None
        self.__line_number = 0

        def add_error(error):
            self.validation_errors.append(error)

        # read in the header lines
        header_lines = list()
        while True:
            self.__next_line__()
            if self.__next_line is not None \
                    and self.__next_line.startswith(MafHeader.HeaderLineStartSymbol):
                header_lines.append(self.__next_line)
            else:
                break
        self.__header = \
            MafHeader.from_lines(
                lines=header_lines,
                validation_stringency=self.validation_stringency)

        for error in self.__header.validation_errors:
            add_error(error)

        # get the column names
        if self.__next_line is not None:
            column_names = self.__next_line.split(MafRecord.ColumnSeparator)
            self.__next_line__()
        else:
            column_names = None

        # update the scheme
        self.__update_scheme__(scheme=scheme, column_names=column_names)

        # validate the column names against the scheme
        if column_names is not None:
            # match the column names against the scheme
            scheme_column_names = self.__scheme.column_names()
            if len(column_names) != len(scheme_column_names):
                add_error(MafValidationError(
                    MafValidationErrorType.SCHEME_MISMATCHING_NUMBER_OF_COLUMN_NAMES,
                    "Found '%d' columns but expected '%d'" %
                    (len(column_names), len(scheme_column_names)),
                    line_number=self.__line_number - 1
                ))
            else:
                for i, (column_name, scheme_column_name) in \
                        enumerate(zip(column_names, scheme_column_names)):
                    if column_name != scheme_column_name:
                        add_error(MafValidationError(
                            MafValidationErrorType.SCHEME_MISMATCHING_COLUMN_NAMES,
                            "Found column with name '%s' but expected '%s' for "
                            "the '%d'th column" %
                            (column_name, scheme_column_name, i + 1),
                            line_number=self.__line_number - 1
                        ))
        else:
            add_error(MafValidationError(
                MafValidationErrorType.HEADER_MISSING_COLUMN_NAMES,
                "Found no column names",
                line_number=self.__line_number+1
            ))

        # process validation errors so far
        MafValidationError.process_validation_errors(
            validation_errors=self.validation_errors,
            validation_stringency=self.validation_stringency,
            name=self.__class__.__name__,
            logger=self.__logger
        )

    def __update_scheme__(self, scheme=None, column_names=None):
        def add_error(error):
            self.validation_errors.append(error)

        self.__scheme = self.__header.scheme()

        # Set the scheme if given, but check that they match, otherwise,
        # add an error
        if scheme is not None:
            if self.__scheme is not None \
                    and scheme.version() != self.__scheme.version():
                add_error(MafValidationError(
                    MafValidationErrorType.HEADER_MISMATCH_SCHEME,
                    "Version in the header '%s' did not match the expected "
                    "version '%s'" %
                    (self.__scheme.version(), scheme.version())
                ))
            self.__scheme = scheme

        # If there are column names, and either there is no scheme or the scheme
        # is the "no restrictions anything goes" scheme, then use the "no
        # restrictions" scheme with the given column names.
        if column_names is not None and \
                (self.__scheme is None
                 or isinstance(self.__scheme, NoRestrictionsScheme)):
            if self.validation_stringency is not ValidationStringency.Silent:
                self.__logger.warn(
                    "No matching scheme was found in the header, defaulting "
                    "to the least restrictive scheme.")
            self.__scheme = NoRestrictionsScheme(column_names=column_names)

    def __next_line__(self):
        try:
            self.__next_line = next(self.__iter).rstrip("\r\n")
            self.__line_number += 1
        except StopIteration:
            self.__next_line = None

    def header(self):
        """Get the file header."""
        return self.__header

    def close(self):
        """Closes the reader and the provided closeable if any"""
        if self.__closeable is not None:
            self.__closeable.close()

    def __iter__(self):
        return self

    def next(self):
        return self.__next__()

    def __next__(self):
        """Gets the next ``MafRecord``.  Raises a ``StopIteration`` when no
        more records can be read."""
        if self.__next_line is None:
            raise StopIteration

        record = MafRecord.from_line(
            line=self.__next_line,
            scheme=self.__scheme,  # always use the scheme
            line_number=self.__line_number,
            validation_stringency=self.validation_stringency
        )

        for error in record.validation_errors:
            self.validation_errors.append(error)

        self.__next_line__()

        return record

    def scheme(self):
        """Returns the scheme used to while reading."""
        return self.__scheme

    @classmethod
    def reader_from(cls, path, validation_stringency=None, scheme=None):
        """Create a reader that reads from the given path."""
        if path.endswith(".gz"):
            handle = gzip.open(path, "rt")
        else:
            handle = open(path, "r")
        lines = (line.rstrip("\r\n") for line in handle)
        return cls(lines=lines, closeable=handle,
                   validation_stringency=validation_stringency,
                   scheme=scheme)
