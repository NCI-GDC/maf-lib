"""This modules implements a container type for a column value in a MafRecord.

* MafColumnRecord        generic container for storing key and value pairs for
                         a given column in a MafRecord.
* MafCustomColumnRecord  a MafColumnRecord to simplify the creation of
                         sub-classes that wish to constrain both the type and
                         value of the column.
"""
import abc

from maflib.util import abstractclassmethod
from maflib.validation import MafValidationErrorType, MafValidationError


class MafColumnRecord(object):
    """
    A generic container for storing key and value pairs for a given column in a
    MafRecord.  Provides methods to validate the value of the column,
    determine if the value is equal to a null value.

    Sub-classes should override the
    :func:``~maflib.column.MafColumnRecord.__nullable_dict__`` method to give
    the values that should be treated as null.
    """
    def __init__(self, key, value, column_index=None, description=None):
        """
        :param key: the name of the column
        :param value: the value of the column
        :param column_index: optionally the zero-based index of the column
        :param description: optionally any description about the column
        """
        self.key = key
        self.value = value
        self.column_index = column_index
        self.description = description
        self.validation_errors = list()

    def validate(self, reset_errors=True, scheme=None, line_number=None):
        """
        Validates that the value is of the correct type and an acceptable
        value.
        :return: a list of validation errors found, if any.
        """

        if reset_errors:
            self.validation_errors = list()

        if scheme:
            def add_errors(error):
                """Adds an error"""
                self.validation_errors.append(error)

            scheme_column_index = scheme.column_index(name=self.key)
            scheme_column_class = scheme.column_class(name=self.key)

            if scheme_column_index is None:
                add_errors(MafValidationError(
                    MafValidationErrorType.SCHEME_MISMATCHING_COLUMN_NAMES,
                    "No column '%s' present in the scheme '%s'"
                    % (self.key, scheme.version()),
                    line_number=line_number
                ))
            elif self.column_index is not None and scheme_column_index != \
                    self.column_index:
                add_errors(MafValidationError(
                    MafValidationErrorType.RECORD_COLUMN_OUT_OF_ORDER,
                    "Column with name '%s' was found in the %dth column"
                    ", but expected the %dth column with scheme "
                    "'%s''" % (self.key, self.column_index,
                               scheme_column_index, scheme.version()),
                    line_number=line_number
                ))
            elif not isinstance(self, scheme_column_class):
                add_errors(MafValidationError(
                    MafValidationErrorType.RECORD_COLUMN_WRONG_FORMAT,
                    "Column with name '%s' is in the wrong format. "
                    "Found '%s' expected '%s'" %
                    (self.key, str(self.__class__),
                     str(scheme_column_class)),
                    line_number=line_number
                ))

        return self.validation_errors

    def is_null(self):
        """
        :return: ``True`` if the value is a "null" value, ``False`` otherwise
        """
        values = self.__nullable_values__()
        if values is None:
            return False
        else:
            return self.value in values

    @classmethod
    def build(cls, name, value, column_index=None, description=None,
              scheme=None):
        """
        If ``scheme`` is given, then the the appropriate column type will be 
        built by matching the provided name with the column name in the 
        scheme.  Otherwise, a column of type ``MafColumnRecord`` will be
        returned.
        :return: builds a ``MafColumnRecords`` from the given string.  Raises a
        ``ValueError`` if there was a formatting error.
        """
        if scheme:
            scheme_column_index = scheme.column_index(name=name)
            if not scheme_column_index:
                raise KeyError(
                    "Column with name '%s' not found in scheme '%s'" %
                    (name, str(scheme))
                )
            elif not column_index is None \
                    and column_index != scheme_column_index:
                raise ValueError(
                    "Mismatch column index: found '%s', expected '%s'" %
                    (str(column_index), str(scheme_column_index))
                )
            # NB: do not pass the scheme!
            return scheme.column_class(name=name) \
                .build(
                name=name,
                value=value,
                column_index=scheme_column_index,
                description=description
            )
        else:
            return MafColumnRecord(
                key=name,
                value=value,
                column_index=column_index,
                description=description
            )

    @classmethod
    def is_nullable(cls):
        """
        :return: ``True`` if this column has a possible "null" value, ``False``
        otherwise.
        """
        return cls.__nullable_values__() is not None

    @classmethod
    def __nullable_dict__(cls):
        """
        :return: a map from the string representation of nullable values to
        the actual nullable value.  For example, an empty string may map to
        ``None``.  ``None`` should be returned if no nullable values exist.
        """
        return None

    @classmethod
    def __nullable_values__(cls):
        """
        This method should not be overridden by sub-classes.
        :return: a list of values that should be treated as "null", ``None``
        otherwise.
        """
        return list(cls.__nullable_dict__().values()) \
            if cls.__nullable_dict__() is not None else None

    @classmethod
    def __nullable_keys__(cls):
        """
        This method should not be overridden by sub-classes.
        :return: a list of values that should be treated as "null", ``None``
        otherwise.
        """
        return list(cls.__nullable_dict__().keys()) \
            if cls.__nullable_dict__() is not None else None

    def __str__(self):
        if self.value is None:
            nullable_dict = self.__nullable_dict__()
            if nullable_dict is not None:
                value = next((key for key, value in nullable_dict.items()
                              if value == self.value), None)
            else:
                value = self.value
            return "" if value is None else str(value)
        else:
            return str(self.value)


class MafCustomColumnRecord(MafColumnRecord):
    """
    A MafColumnRecord to simplify the creation of sub-classes that wish to
    constrain both the type and value of the column.

    Sub-classes should implement the ``__build__`` and ``__validate__``
    methods.
    """

    __metaclass__ = abc.ABCMeta

    @classmethod
    @abstractclassmethod
    def __build__(cls, value):
        """
        Builds the column's value from the given string.  Raises a
        ``ValueError`` if there was a formatting error.  Any logic about
        converting the value or type should be done here.
        """

    @classmethod
    def build(cls, name, value, column_index=None, description=None,
              scheme=None):
        """
        This method should not be overridden by sub-classes.

        Builds the column's value from the given string.  Raises a
        ``ValueError`` if there was a formatting error.  The passed value is
        first checked to see if it is in the ``__nullable_dict__`` dictionary,
        and if so, the value in the dictionary is returned.  Otherwise,
        the ``__build__`` method is called.
        """
        if scheme:
            return super(MafCustomColumnRecord, cls).build(
                name=name,
                value=value,
                column_index=column_index,
                description=description,
                scheme=scheme
            )
        nullable_dict = cls.__nullable_dict__()
        if nullable_dict is not None and value in nullable_dict:
            built_value = nullable_dict[value]
        else:
            built_value = cls.__build__(value=value)
        return cls(
            key=name,
            value=built_value,
            column_index=column_index,
            description=description
        )

    def __validate__(self):
        """
        A sub-class should implement this to perform any custom validation on
        the type and value of the value returned by ``__build__``.
        :return: None if the column's value is valid, otherwise a
        string message to return the user.
        """
        return None

    def validate(self, reset_errors=True, scheme=None, line_number=None):
        """
        This method should not be overridden by sub-classes.

        Checks to see if the value is one of the nullable values.  If not,
        calls ``__validate__``.  If no message was returned, calls ``validate``
        on the super-class.
        :return: a list of validation errors, if any.
        """
        if reset_errors:
            self.validation_errors = list()
        nullable_values = self.__nullable_values__()
        if nullable_values is not None and self.value in nullable_values:
            msg = None
        else:
            msg = self.__validate__()
        if msg is not None:
            error = MafValidationError(
                MafValidationErrorType.RECORD_COLUMN_WRONG_FORMAT,
                "%s in column with name '%s'" % (msg, self.key),
                line_number=line_number)
            self.validation_errors.append(error)
        return super(MafCustomColumnRecord, self).validate(
            reset_errors=False,  # we reset above!
            scheme=scheme, line_number=line_number)

    def __str__(self):
        """Delegates the conversion to a string for non-null values to
        __string_it__()"""
        super_str = super(MafCustomColumnRecord, self).__str__()
        if super_str:
            return self.__string_it__()
        else:
            return super_str

    def __string_it__(self):
        """Sub-classes can override this method to print a string when the
        value is not null"""
        return str(self.value)
