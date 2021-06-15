from collections import OrderedDict
from typing import Iterable, NoReturn

from maflib.column import MafColumnRecord
from maflib.schemes.base import MafScheme


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
