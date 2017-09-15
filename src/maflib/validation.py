"""A module containing classes used for validating MAF files and data types.

* MafFormatException      an exception when the MAF is mis-formatted
* MafValidationError      stores a specific validation error and type
* MafValidationErrorType  an enumeration of types of validation errors
* ValidationStringency    an enumeartion for the stringency in which to validate
"""

from enum import Enum, unique

from maflib.logger import Logger


class MafFormatException(Exception):
    """
    Thrown when reading or writing MAF files after finding a formatting error.
    """

    def __init__(self, tpe, message, line_number=None):
        super(MafFormatException, self).__init__(message)
        self.tpe = tpe
        self.line_number = line_number
        self.message = message

    def __str__(self):
        return self.message


class MafValidationError(object):
    """Stores a specific validation error and type """
    __IgnoringMessageFormat = "Ignoring MAF validation error: %s"

    @staticmethod
    def ignore_message(validation_error):
        """Returns a string message for when an error will be ignored"""
        return MafValidationError.__IgnoringMessageFormat \
               % str(validation_error)

    def __init__(self, tpe, message, line_number=None):
        self.tpe = tpe
        self.message = message
        self.line_number = line_number

    def __str__(self):
        if self.line_number:
            return "%s: On line number %d: %s" % \
                   (self.tpe.name, self.line_number, self.message)
        else:
            return "%s: %s" % (self.tpe.name, self.message)

    @staticmethod
    def process_validation_errors(validation_errors, validation_stringency,
                                  name=None, logger=Logger.RootLogger):
        """Handles a list of errors given a validation stringency.

        If the validation stringency is ``Silent`` or no errors are given,
        then nothing is done.  If the validation stringency is ``Lenient``, then
        the errors are logged.  If the validation stringency is ``Strict``,
        then the a ``MafFormatException`` is thrown using the first error found.
        """
        if validation_errors \
                and not validation_stringency == ValidationStringency.Silent:
            if validation_stringency == ValidationStringency.Strict:
                error = validation_errors[0]
                raise MafFormatException(
                    tpe=error.tpe,
                    message=str(error),
                    line_number=error.line_number
                )
            else:
                assert validation_stringency == ValidationStringency.Lenient
                for error in validation_errors:
                    logger.warning(MafValidationError.ignore_message(error))

    # TODO: tpe should have a severity
    # class Severity(Enum):
    #    '''
    #    The severity of an :class:`Error`
    #    '''
    #    Warning = "Warning"
    #    Error   = "Error"


@unique
class MafValidationErrorType(Enum):
    """
    The type of validation error.
    """
    HEADER_MISSING = \
        "The header is missing"
    HEADER_LINE_MISSING_START_SYMBOL = \
        "The header line is missing the start symbol at the start of the line"
    HEADER_LINE_MISSING_SEPARATOR = \
        "The header line is missing the space separator"
    HEADER_LINE_EMPTY_KEY = \
        "The header line's key is empty"
    HEADER_LINE_EMPTY_VALUE = \
        "The header line's value is empty"
    HEADER_DUPLICATE_KEYS = \
        "The header has duplicate keys"
    HEADER_MISSING_VERSION = \
        "The header has no version"
    HEADER_UNSUPPORTED_VERSION = \
        "The header has an unsupported version"
    HEADER_MISSING_ANNOTATION_SPEC = \
        "The header has no annotation spec"
    HEADER_UNSUPPORTED_ANNOTATION_SPEC = \
        "The header has an unsupported annotation specification"
    HEADER_UNSUPPORTED_SORT_ORDER = \
        "The header has an unsupported sort order"
    HEADER_MISMATCH_SCHEME = \
        "The header's scheme mismatches the current scheme"
    HEADER_MISSING_COLUMN_NAMES = \
        "The header has no column names"
    HEADER_MISMATCHING_COLUMN_NAMES =\
        "The header's column names mismatch the expected column names"
    RECORD_COLUMN_WITH_NO_VALUE = \
        "The record has no value"
    RECORD_OUT_OF_SYNC =\
        "The record is out of sync (internal error)"
    RECORD_COLUMN_INDEX_OUT_OF_SYNC = \
        "The column index is out of sync (internal error)"
    RECORD_MISMATCH_NUMBER_OF_COLUMNS = \
        "The record has an unexpected number of columns"
    RECORD_COLUMN_WRONG_FORMAT = \
        "The record's column is in the wrong format"
    RECORD_INVALID_COLUMN_VALUE = \
        "The record's column has an invalid value"
    RECORD_INVALID_COLUMN_NAME = \
        "The record's column has an invalid name"
    RECORD_COLUMN_OUT_OF_ORDER = \
        "The record's column is at the wrong offset/index"
    SCHEME_MISMATCHING_NUMBER_OF_COLUMN_NAMES = \
        "The number of columns found differs from the scheme"
    SCHEME_MISMATCHING_COLUMN_NAMES = \
        "The column name differs from the scheme"


@unique
class ValidationStringency(Enum):
    """
    The strictness when reading, writing, or validating a MAF file.
    """
    Strict = 1
    Lenient = 2
    Silent = 3
