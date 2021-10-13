"""A module containing schemes for a MAF file.  A scheme determines the
number of columns, their names, and their expected values.  A scheme can be
determined from the version and annotation specification in the MAF header's
version and annotation specification pragmas respectively.  It should not be
modified after being instantiated.

* MafScheme                  the base scheme all schemes should implement
* NoRestrictionsScheme       a scheme that has no restrictions on the column
                             names and values.
* GdcV1_0_0_BasicScheme      the GDC v1.0.0 basic scheme
* GdcV1_0_0_PublicScheme     the GDC v1.0.0 public scheme
* GdcV1_0_0_ProtectedScheme  the GDC v1.0.0 protected scheme
"""
import abc
from collections import OrderedDict
from typing import Iterable, List, NoReturn, Optional, Union

from maflib.column import MafColumnRecord


class MafScheme:
    """The base scheme all schemes should implement.

    Sub-classes should implement ``version()``, ``annotation``, and
    ``__column_dict__()``.
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, column_dict: dict = None, column_desc: dict = None):
        """Create a new MafScheme.  If a ``column_dict`` is supplied,
        use that one, otherwise, use the one from ``__column_dict__``."""
        if column_dict is None:
            column_dict = self.__column_dict__()
        if column_desc is None:
            column_desc = self.__column_desc__()
        self.__column_name_to_column_class = OrderedDict(
            (name, cls) for name, cls in column_dict.items()
        )
        self.__column_name_to_column_index = OrderedDict(
            (name, i) for i, (name, _) in enumerate(column_dict.items())
        )
        self.__column_name_to_column_desc = OrderedDict(
            (name, desc) for name, desc in column_desc.items()
        )

    def column_class(self, name: str):  # type: ignore
        """Get the class for the column with the given name"""
        return self.__column_name_to_column_class.get(name, None)

    def column_index(self, name: str) -> Optional[int]:
        """Get the zero-based index for the column with the given name"""
        return self.__column_name_to_column_index.get(name, None)

    def column_description(self, name: str) -> Optional[str]:
        """Get the description of the column with the given name"""
        return self.__column_name_to_column_desc.get(name, None)

    def column_names(self) -> List[str]:
        """Get names of the columns in order of column index"""
        return list(self.__column_name_to_column_class.keys())

    def column_descriptions(self) -> List[str]:
        """Get description of the columns in order of column index"""
        return list(self.__column_name_to_column_desc.keys())

    @classmethod
    def is_basic(cls) -> bool:
        """Returns true if the scheme is a "basic" scheme, false otherwise."""
        version = cls.version()
        annotation = cls.annotation_spec()
        if version is not None and annotation is not None:
            return cls.version() == cls.annotation_spec()
        else:
            return False

    @classmethod
    @abc.abstractmethod
    def version(cls) -> str:
        """
        :return: the canonical version string
        """

    @classmethod
    @abc.abstractmethod
    def annotation_spec(cls) -> str:
        """
        :return: the annotation specification
        """

    @classmethod
    @abc.abstractmethod
    def __column_dict__(cls) -> Union[dict, NoReturn]:
        """
        :return: A mapping between column name and class for the column type.
        """

    @classmethod
    def __column_desc__(cls) -> dict:
        """
        :return: A mapping between column name and column description.
        """
        return OrderedDict(
            (name, "No description for column '%s'" % name)
            for name in cls.__column_dict__().keys()  # type: ignore
        )

    def __str__(self) -> str:
        return self.version()

    def __len__(self) -> int:
        """
        :return: The number of columns in this scheme
        """
        return len(self.__column_name_to_column_class)


class NoRestrictionsScheme(MafScheme):
    """A MafScheme with no restrictions on the column names and values.  A
    list of column names should be ge given when constructed."""

    def __init__(self, column_names: Iterable[str]):
        column_dict = OrderedDict((name, MafColumnRecord) for name in column_names)
        column_desc = OrderedDict((name, "") for name in column_names)
        super(NoRestrictionsScheme, self).__init__(
            column_dict=column_dict, column_desc=column_desc
        )

    @classmethod
    def version(cls) -> str:
        return "no-version"

    @classmethod
    def annotation_spec(cls) -> str:
        return "no-annotation-specification"

    @classmethod
    def __column_dict__(cls) -> NoReturn:
        raise ValueError("__column_dict__ may not be called on " "NoRestrictionsScheme")

    @classmethod
    def __column_desc__(cls) -> NoReturn:
        raise ValueError("__column_desc__ may not be called on " "NoRestrictionsScheme")
