"""A module to store a single MAF file line, or more specifically,
the annotation values for a single mutation.

* MafRecord  stores annotations for a single mutation.
"""

import logging
from collections.abc import MutableMapping
from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional, Union

from maflib.column import MafColumnRecord
from maflib.locatable import LocatableByAllele
from maflib.logger import Logger
from maflib.validation import (
    MafValidationError,
    MafValidationErrorType,
    ValidationStringency,
)

if TYPE_CHECKING:
    from maflib.schemes import MafScheme

TKey = Optional[Union[int, MafColumnRecord, str]]


class MafRecord(MutableMapping, LocatableByAllele):
    """
    A MAF record, representing one line in a MAF file, storing annotations for
    a single mutation.

    No requirement on the number of columns, their names, their order, or their
    values is made here.

    Use the `validate` method to validate the record once the record has all
    desired columns set.
    """

    ColumnSeparator = "\t"

    def __init__(
        self,
        line_number: Optional[int] = None,
        validation_stringency: ValidationStringency = ValidationStringency.Silent,
    ):
        self.__line_number = line_number
        self.__columns_dict: Dict[str, MafColumnRecord] = dict()
        self.__columns_list: List[Optional[MafColumnRecord]] = list()
        self.validation_stringency = (
            ValidationStringency.Silent
            if (validation_stringency is None)
            else validation_stringency
        )
        self.validation_errors: List[MafValidationError] = list()
        super(MafRecord, self).__init__(
            chromosome=None, start=None, end=None, ref=None, alts=None
        )

    def __getitem__(self, key: TKey) -> Optional[MafColumnRecord]:
        """
        :param key: The key can be one of four things:
        1. If an `int`, it is assumed to be the `column_index` of the column.
        2. If a `MafColumnRecord`, then use the `key` from the column.
        3. If `None`, always return `None`.
        4. Otherwise, it should be a string representing the `name` of the
        column.
        :return:
        """
        if isinstance(key, int):
            column_index = int(key)
            if column_index < 0 or len(self.__columns_list) <= column_index:
                raise KeyError
            return self.__columns_list[column_index]
        elif isinstance(key, MafColumnRecord):
            return self.__columns_dict[key.key]
        elif key is not None:
            if not isinstance(key, str):
                raise TypeError
            return self.__columns_dict[key]
        else:
            return None

    @staticmethod
    def __get_key_from_int(key: Union[str, int], column: MafColumnRecord) -> str:
        """Returns the name that should be used for the column and sets the
        column index if not already set"""
        column_index = int(key)
        if column_index < 0:
            raise KeyError
        # set the column_index on column if not already set, otherwise
        # ensure they are the same
        if column.column_index is None:
            column.column_index = column_index
        elif column_index != column.column_index:
            raise ValueError(
                f"Column index mismatch: {column.column_index} is not {column_index}"
            )
        return column.key

    @staticmethod
    def __get_key_from_column(
        key_as_column: MafColumnRecord, column: MafColumnRecord
    ) -> str:
        """Returns the name that should be used for the column ensuring the
        names for the two given columns are the same"""
        # make sure the keys are the same
        if column.key != key_as_column.key:
            raise ValueError(
                f"Column name mismatch '{column.key}' is not '{key_as_column.key}'"
            )
        return key_as_column.key

    def __setitem__(self, key: Union[int, str], column: MafColumnRecord) -> None:
        """If a record already exists with the column name `key`, we either
        check that the `column_index`es are the same, or set the `column_index`
        if it is not set on the record.  Otherwise, if the `column_index` is not
        set and no existing record is found with the column name `key`, then
        append it, and set `column_index` in `column`.

        If the `column_index` is greater than the length, then extend the number
        of columns, inserting `None` for values for any columns between the old
        and new length; these columns will have no name.

        :param key: The key may be one of four things: 1. If an `int`,
        it is assumed to be the `column_index` of the column.  The
        `column_index` of`column` will be set to `int(key)` if not already set.
        If already set, then `column.column_index` should equal `int(key)`. 2.
        If an `MafColumnRecord`, then the `MafColumnRecord` should have the same
        `key` as the provided column. 3. If `None`, then `None` will always be
        returned. 4. Otherwise, it should be the column name, and be the same as
        the `key` in the provided column.
        :param column: an instance of `MafColumnRecord`."""
        if not isinstance(column, MafColumnRecord):
            raise TypeError(f"{type(column)} is not 'MafColumnRecord'")

        if isinstance(key, int):
            key = self.__get_key_from_int(key, column)
        elif isinstance(key, MafColumnRecord):
            # make sure the keys are the same
            key = self.__get_key_from_column(key, column)
        elif not isinstance(key, str):
            raise TypeError("Column name must be a string")
        elif column.key != key:
            raise ValueError(
                f"Adding a column with name '{column.key}' but key was '{key}'"
            )
        assert key == column.key

        # if there already is a record with the same key, make sure that it has
        # the same column index, otherwise set the column index if the current
        # record doesn't have one.  If there is no record with the same and the
        # column index is not set, set it as the next column in the list.
        if key in self.__columns_dict:
            if column.column_index is None:
                column.column_index = self.__columns_dict[key].column_index
            else:
                if self.__columns_dict[key].column_index != column.column_index:
                    raise ValueError(
                        f"Existing column's index '{self.__columns_dict[key].column_index}' does not match replacement column's index '{column.column_index}'"
                    )
        elif column.column_index is None:
            # set the column index to the next column
            column.column_index = len(self.__columns_list)
        self.__columns_dict[key] = column
        assert column.column_index is not None

        # extend the list if the index is out of range
        if len(self) <= column.column_index:
            num_more = column.column_index - len(self) + 1
            self.__columns_list.extend([None] * num_more)
        # Developer Note: due to padding, the number of items in the dictionary
        # may be less than the number of items in the list.  Use validate to
        # catch this later.
        self.__columns_list[column.column_index] = column

    def __delitem__(self, key: TKey) -> None:
        """
        Deletes the item with the given key.
        :param key: can be any key type supported by `__getitem__`, except
        `None`.
        """
        column = self[key]
        if not column:
            raise KeyError
        del self.__columns_dict[column.key]
        if column.column_index == len(self.__columns_list) - 1:
            del self.__columns_list[column.column_index]
            while self.__columns_list and self.__columns_list[-1] is None:
                del self.__columns_list[-1]
        else:
            self.__columns_list[column.column_index] = None  # type: ignore

    def __iter__(self) -> Iterator[Any]:
        """
        :return: an iterable over all keys in this record.  `None` are
        substituted for missing columns.
        """
        return iter(
            [(column.key if column else None) for column in self.__columns_list]
        )

    def __len__(self) -> int:
        """
        :return: the number of columns, including columns that may have missing
         values.
        """
        return len(self.__columns_list)

    def __str__(self) -> str:
        """
        :return: The MAF record formatted as though it would be in a MAF file.
          No newline is appended.
        """
        records = [str(record) for record in self.__columns_list]
        return MafRecord.ColumnSeparator.join(records)

    # FIXME: Enum
    @property  # type: ignore
    def chromosome(self):  # type: ignore
        """Returns the chromosome name"""
        return self["Chromosome"].value

    @property  # type: ignore
    def start(self):  # type: ignore
        """Returns the start position"""
        return self["Start_Position"].value

    @property  # type: ignore
    def end(self):  # type: ignore
        """Returns the end position"""
        return self["End_Position"].value

    @property
    def ref(self):  # type: ignore
        """Returns the reference allele"""
        return self["Reference_Allele"].value

    @property
    def alts(self) -> list:
        """Returns a list of valid alternate alleles"""
        return [self["Tumor_Seq_Allele2"].value]  # type: ignore

    def add(self, column: MafColumnRecord) -> 'MafRecord':
        """Add the column to the record"""
        return self.__iadd__(column)

    def __iadd__(self, column: MafColumnRecord) -> 'MafRecord':
        """Add the column to the record"""
        self.__setitem__(column.key, column)
        return self

    def value(self, key: TKey) -> Any:
        """Gets the value for the column with the given name"""
        try:
            return self[key].value  # type: ignore
        except KeyError:
            return None

    def column_values(self) -> List[Optional[Any]]:
        """Gets the values for all columns in order."""
        return [
            (column.value if column is not None else None) for column in self.values()
        ]

    def validate(
        self,
        validation_stringency: Optional[ValidationStringency] = None,
        logger: logging.Logger = Logger.RootLogger,
        reset_errors: bool = True,
        scheme: Optional['MafScheme'] = None,
    ) -> List[MafValidationError]:
        """
        Collects a list of validation errors.
        :return: the list of validation errors, if any.
        """
        if reset_errors:
            self.validation_errors = list()

        found_none_column = False

        if not validation_stringency:
            validation_stringency = self.validation_stringency

        def add_errors(error: MafValidationError) -> None:
            self.validation_errors.append(error)

        # Validate the # of columns against the given scheme

        if scheme and len(scheme) != len(self):
            add_errors(
                MafValidationError(
                    MafValidationErrorType.RECORD_MISMATCH_NUMBER_OF_COLUMNS,
                    f"Found '{len(self)}' columns but expected '{len(scheme)}'",
                )
            )

        # find any columns that have None in the list or dictionary
        for i, column in enumerate(self.__columns_list):
            if not column:
                # NB: I am not sure if this that useful of an error to report
                # when the column could not be built successfully?
                found_none_column = True
                add_errors(
                    MafValidationError(
                        MafValidationErrorType.RECORD_COLUMN_WITH_NO_VALUE,
                        f"Column '{i+1}' had no value",
                        line_number=self.__line_number,
                    )
                )
            else:
                # add any validation errors from the column itself.
                self.validation_errors.extend(
                    column.validate(reset_errors=reset_errors, scheme=scheme)  # type: ignore
                )

        # if we did not find any None columns, then do a bunch of internal
        #  self-consistency checking.
        if not found_none_column:
            # double-check the dictionary for columns with None values.
            for name in self.__columns_dict:
                assert self.__columns_dict[name] is not None
            # validate we have the same # of columns in the list as in the dict
            assert len(self.__columns_dict) == len(self.__columns_list)
            # validate we have the same columns in the list as in the dict
            assert (
                sorted(self.__columns_dict.values(), key=lambda r: r.column_index)  # type: ignore
                == self.__columns_list
            )
            # ensure that all records' column_index match the index in the list
            for (column_index, column) in enumerate(self.__columns_list):
                assert column_index == column.column_index  # type: ignore

        # TODO: validate cross-column constraints (ex. Mutation_Status)
        # TODO: validate that chromosome/start/end are defined

        # process validation errors
        MafValidationError.process_validation_errors(
            validation_errors=self.validation_errors,
            validation_stringency=validation_stringency,
            logger=logger,
        )

        return self.validation_errors

    @classmethod
    def from_line(
        cls,
        line: str,
        column_names: Optional[List[str]] = None,
        scheme: Optional['MafScheme'] = None,
        line_number: Optional[int] = None,
        validation_stringency: ValidationStringency = ValidationStringency.Strict,
        logger: logging.Logger = Logger.RootLogger,
    ) -> 'MafRecord':
        """
        Parses a record from a single tab-delimited line.
        :param column_names: the expected names of the columns, in order,
        otherwise will use the scheme.
        :param line: the line to parse.
        :param scheme: an optional MafScheme
        :param line_number: the optional line number.
        :param validation_stringency: the optional validation stringency for
        the record
        :param logger the logger to which to write errors
        :return:
        """
        record = cls(
            line_number=line_number, validation_stringency=validation_stringency
        )

        if column_names is None:
            if scheme is None:
                raise ValueError("Either column_names or scheme must be given")
            column_names = scheme.column_names()

        def add_errors(error: MafValidationError) -> None:
            record.validation_errors.append(error)

        column_values = line.rstrip("\r\n").split(cls.ColumnSeparator)

        if len(column_names) != len(column_values):
            add_errors(
                MafValidationError(
                    MafValidationErrorType.RECORD_MISMATCH_NUMBER_OF_COLUMNS,
                    f"Found '{len(column_values)}' columns but expected '{len(column_names)}'",
                    line_number=line_number,
                )
            )
            record.validate(logger=logger, reset_errors=False)

            return record

        for column_index, (column_name, column_value) in enumerate(
            zip(column_names, column_values)
        ):
            column = None

            scheme_column_class = (
                scheme.column_class(name=column_name) if scheme else None
            )

            # A validation error will be found later if we don't find the
            # column name
            if scheme_column_class is None:
                column = MafColumnRecord(
                    key=column_name, value=column_value, column_index=column_index
                )
            else:
                try:
                    scheme_column_class = scheme.column_class(name=column_name)  # type: ignore
                    column = scheme_column_class.build(  # type: ignore
                        name=column_name,
                        value=column_value,
                        column_index=column_index,
                    )
                except Exception as error:
                    add_errors(
                        MafValidationError(
                            MafValidationErrorType.RECORD_INVALID_COLUMN_VALUE,
                            f"Could not build column '{column_index+1}' with name '{column_name}' scheme '{scheme.version()}': {error}",  # type: ignore
                            line_number=line_number,
                        )
                    )

            if column is not None:
                column_validation_errors = column.validate(
                    scheme=scheme, line_number=line_number
                )
                record.validation_errors.extend(column_validation_errors)  # type: ignore
                if len(column_validation_errors) == 0:
                    record[column_name] = column

        # process validation errors
        record.validate(logger=logger, reset_errors=False)

        return record
