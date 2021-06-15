"""This module contains an implementation of a sort-orders.
"""
import abc
from functools import total_ordering
from typing import (
    Any,
    Callable,
    Generic,
    Iterator,
    List,
    NoReturn,
    Optional,
    Type,
    Union,
)

from typing_extensions import TypeAlias

from maflib.locatable import Locatable
from maflib.record import MafRecord
from maflib.util import abstractclassmethod


@total_ordering  # type: ignore
class SortOrderKey:
    """A container for the key used to sort MafRecords.  Sub-classes should
    implement the __cmp__ method."""

    __metaclass__ = abc.ABCMeta

    def __init__(self, *args: Any, **kwargs: Any):
        pass

    def __lt__(self, other: 'SortOrderKey') -> bool:  # type: ignore[override]
        """Compare less than"""
        return self.__cmp__(other) < 0

    def __eq__(self, other: 'SortOrderKey') -> bool:  # type: ignore[override]
        """Compare equal"""
        return self.__cmp__(other) == 0

    @abc.abstractmethod
    def __cmp__(self, other: 'SortOrderKey') -> int:
        """Compares two objects, returning -1 if this is less than the other, 0
        if they are equal, and 1 otherwise."""

    @classmethod
    def compare(cls, this: Any, that: Any) -> int:
        """Convenience method for comparing two objects of the same type that
        have a total ordering."""
        if this is None and that is None:
            return 0
        elif this is None:
            return 1
        elif that is None:
            return -1
        else:
            return (this > that) - (this < that)


TSortKey = Callable[[Union[MafRecord, Locatable]], SortOrderKey]


class SortOrder:
    """Base class for all sort orders.  Sub-classes should implement name and
    sortKey."""

    __metaclass__ = abc.ABCMeta

    def __init__(self) -> None:
        pass

    @classmethod
    def name(cls) -> str:
        """Returns the order's name."""
        return cls.__name__

    @abc.abstractmethod
    def sort_key(self) -> TSortKey:
        """Function to generate the sort key for sorting records into this
        ordering"""

    # TODO: Implement this better
    @classmethod
    def all(cls) -> list:
        """Returns the known sort order classes."""
        return [Unknown, Unsorted, BarcodesAndCoordinate, Coordinate]

    @classmethod
    def find(cls, sort_order_name: str) -> Type['SortOrder']:
        """Returns the sort order class by name.  Throws an exception if
        none was found"""
        sort_order = next(
            iter([so for so in SortOrder.all() if so.name() == sort_order_name]), None
        )
        if not sort_order:
            sort_orders = ", ".join([s.name() for s in SortOrder.all()])
            raise ValueError(
                "Could not find sort order '%s', options: %s"
                % (sort_order_name, sort_orders)
            )
        return sort_order

    def __str__(self) -> str:
        return self.name()


class Unknown(SortOrder):
    """Defines a sort order"""

    def sort_key(self) -> NoReturn:
        """Returns the sort key, which is not implemented as sorting is not
        valid for the Unknown sort order."""
        raise NotImplementedError("Sorting not supported for Unknown order.")


class Unsorted(SortOrder):
    """Defines a sort order based on the chromosome, start position, and end
    position, in that order."""

    def sort_key(self) -> NoReturn:
        """Returns the sort key, which is not implemented as sorting is not
        valid for the Unsorted sort order."""
        raise NotImplementedError("Sorting not supported for Unsorted order.")


class _CoordinateKey(SortOrderKey, Locatable):
    """A little class that aids in comparing records based on chromosome,
    start position, and end position"""

    def __init__(self, record: Locatable, contigs: List[str]):
        if not issubclass(record.__class__, Locatable):
            raise ValueError(
                "Record of type '%s' is not a subclass of "
                "'Locatable'" % record.__class__.__name__
            )
        chromosome = record.chromosome
        if contigs:
            try:
                chromosome = contigs.index(chromosome)  # type: ignore
            except ValueError:
                raise ValueError(
                    "Could not find contig '%s' in list of contigs: %s"
                    % (chromosome, ", ".join(contigs))
                )
        Locatable.__init__(self, chromosome, record.start, record.end)

    def __cmp__(self, other: '_CoordinateKey') -> int:  # type: ignore[override]

        diff = self.compare(self.chromosome, other.chromosome)
        if diff == 0:
            diff = self.compare(self.start, other.start)
        if diff == 0:
            diff = self.compare(self.end, other.end)
        return diff

    def __str__(self) -> str:
        return "\t".join(str(s) for s in [self.chromosome, self.start, self.end])


class Coordinate(SortOrder):
    """Defines a sort order based on the chromosome, start position, and end
    position, in that order."""

    def __init__(
        self, fasta_index: Optional[str] = None, contigs: Optional[list] = None
    ):
        """
        provide either fasta_index or contigs

        :param fasta_index: the path to the FASTA index for defining
        ordering across chromosomes.
        :param contigs: list of contigs for ordering
        """
        _contigs = []
        if fasta_index:
            with open(fasta_index) as handle:
                _contigs = [line.strip().split("\t")[0] for line in handle]
        elif contigs:
            assert isinstance(
                contigs, list
            ), "contigs must be a list, but {0} found".format(type(contigs))
            _contigs = contigs
        self._contigs: list = _contigs
        super().__init__()

    @classmethod
    def name(cls) -> str:
        return cls.__name__

    def sort_key(self) -> TSortKey:
        """Function to generate the sort key for sorting records into this
        ordering"""

        def key(record: Locatable) -> _CoordinateKey:
            """Gets the key"""
            return _CoordinateKey(record=record, contigs=self._contigs)

        return key


class _BarcodesAndCoordinateKey(_CoordinateKey):
    """A little class that aids in comparing records based on tumor barcode,
    matched normal barcode, chromosome, start position, and end position"""

    def __init__(self, record: MafRecord, contigs: List[str]):
        self.tumor_barcode = record.value("Tumor_Sample_Barcode")
        self.normal_barcode = record.value("Matched_Norm_Sample_Barcode")
        super(_BarcodesAndCoordinateKey, self).__init__(record, contigs)

    def __cmp__(self, other: '_BarcodesAndCoordinateKey') -> int:  # type: ignore[override]

        diff = self.compare(self.tumor_barcode, other.tumor_barcode)
        if diff == 0:
            diff = self.compare(self.normal_barcode, other.normal_barcode)
        if diff == 0:
            diff = super(_BarcodesAndCoordinateKey, self).__cmp__(other)
        return diff

    def __str__(self) -> str:
        return "\t".join(
            [
                self.tumor_barcode,
                self.normal_barcode,
                super(_BarcodesAndCoordinateKey, self).__str__(),
            ]
        )


class BarcodesAndCoordinate(Coordinate):
    """Defines a sort order based on the tumor barcode, matched normal
    barcode, chromosome, start position, and end position, in that order."""

    def __init__(self, *args: Any, **kwargs: Any):
        super(BarcodesAndCoordinate, self).__init__(*args, **kwargs)

    def sort_key(self) -> TSortKey:
        """Function to generate the sort key for sorting records into this
        ordering"""

        def key(record: MafRecord) -> _BarcodesAndCoordinateKey:
            """Gets the key"""
            return _BarcodesAndCoordinateKey(record=record, contigs=self._contigs)

        return key  # type: ignore


class SortOrderChecker:
    """Checks that the records given are in sorted order"""

    def __init__(self, sort_order: SortOrder):
        self._last_record: Optional[Locatable] = None
        self._sort_f: Optional[TSortKey]
        try:
            self._sort_f = sort_order.sort_key()
        except NotImplementedError:
            self._sort_f = None

    def add(self, record: Locatable) -> 'SortOrderChecker':
        """Check that the given record is in order relative to the previous
        record"""
        return self.__iadd__(record)

    def __iadd__(self, record: Locatable) -> 'SortOrderChecker':
        if self._last_record and self._sort_f:
            rec_key = self._sort_f(record)
            last_rec_key = self._sort_f(self._last_record)
            if rec_key < last_rec_key:
                raise ValueError(f"Records out of order: {self._last_record} {record}")
        self._last_record = record
        return self

    def __del__(self) -> None:
        self._last_record = None
        self._sort_f = None


class SortOrderEnforcingIterator:
    """An iterator that enforces a sort order."""

    def __init__(self, _iter: Iterator[Locatable], sort_order: SortOrder):
        self._checker: SortOrderChecker = SortOrderChecker(sort_order=sort_order)
        self._iter: Iterator = _iter

    def __iter__(self) -> 'SortOrderEnforcingIterator':
        return self

    def next(self) -> Locatable:
        """Gets the next element."""
        return self.__next__()

    def __next__(self) -> Locatable:
        record = next(self._iter)
        self._checker.add(record)
        return record
