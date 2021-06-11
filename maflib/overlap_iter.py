"""This module contains an implementation of a locatables overlapping
iterator.

* LocatableOverlapIterator  allows for jointly iterating over multiple
    iterators and returning the set of locatables that
    overlap between them.
* LocatableByAlleleOverlapIterator Extends `LocatableOverlapIterator` to return
    only those loctables who have the same reference allele as a locatable
    from the **first** iterator, as well as the given relationship between
    the alternate alleles (i.e. equality, intersects, subset).
"""

from enum import Enum, unique
from typing import Callable, Iterator, List, Optional, Type

from maflib.sort_order import BarcodesAndCoordinate, Coordinate, SortOrderKey
from maflib.util import PeekableIterator


class LocatableOverlapIterator:
    """ An iterator over overlapping locatables across multiple `Locatable`s.
    One or more iterators should be given.  The records in each iterator are
    assumed to be sorted by coordinate order (see
    `maflib.sort_order.Coordinate`), which will be verified during
    iteration.

    A list of lists is returned each iteration, with one list of locatables per
    input iterators.  A list of locatables per iterator is returned, since we
    have multiple locatables in one iterator overlapping a locatables in the
    other.  For example, consider the following intervals representing
    locatables on one chromosome:
        iter#1: [1,10], [15,15], [30,40]
        iter#2: [5,25], [50,60]
    then we will return the following
        next#1: [ [[1,10], [15,15]], [[5,25]] ]
        next#2: [ [30,40], [] ]
        next#3: [ [], [[50, 60]] ]
    This scenario happens most frequently with locatables representing MNPs,
    indels, and SVs.
    """

    def __init__(
        self,
        iters: List[Iterator],
        fasta_index: Optional[str] = None,
        contigs: List[str] = None,
        by_barcodes: bool = True,
        peekable_iterator_class: Type[PeekableIterator] = PeekableIterator,
    ):
        """
        :param iters: the list of iterators.
        :param fasta_index: the path to the FASTA index for defining
        ordering across chromosomes.
        :param contigs: the list of contigs to use for sorting instead of
        parsing from FASTA index.
        :param by_barcodes: True to require the same tumor and matched
        normal barcodes for returned locatables, False otherwise
        :param peekable_iterator_class: PeekableIterator class to use when
        traversing individual MAFs. This allows developers to add in custom
        filters and custom handling of MAFs.
        """

        if not by_barcodes:
            _sort_order = Coordinate(fasta_index=fasta_index)
            self._overlap_f = self.__overlaps
        else:
            _sort_order = BarcodesAndCoordinate(
                fasta_index=fasta_index, contigs=contigs
            )
            self._overlap_f = self.__overlaps_with_barcode
        self._sort_order: Coordinate = _sort_order
        self._by_barcodes: bool = by_barcodes

        # Trust, but verify
        _iters = [
            _SortOrderEnforcingIterator(_iter, self._sort_order) for _iter in iters
        ]
        self._iters: List[PeekableIterator] = [
            peekable_iterator_class(_iter) for _iter in _iters
        ]

        self._sort_key: SortOrderKey = self._sort_order.sort_key()

    @classmethod
    def __overlaps_with_barcode(cls, min_key, cur_key) -> bool:
        return (
            min_key.tumor_barcode == cur_key.tumor_barcode
            and min_key.normal_barcode == cur_key.normal_barcode
            and cls.__overlaps(min_key, cur_key)
        )

    @classmethod
    def __overlaps(cls, min_key, cur_key) -> bool:
        # NB: we assume that min_key.start <= cur_key.start
        # NB: ignores tumor and normal barcode
        return (
            min_key.chromosome == cur_key.chromosome
            and min_key.start <= cur_key.start <= min_key.end
        )

    def __iter__(self) -> 'LocatableOverlapIterator':
        return self

    def next(self):
        """Gets the next set of overlapping locatables."""
        return self.__next__()

    def __to_sort_key(self, rec):
        return self._sort_key(rec) if rec else None

    def __next__(self):
        # 1. find the record with the smallest key.
        keys = [self.__to_sort_key(_iter.peek()) for _iter in self._iters]
        # check that we have at least one _iter that return a non-None value
        next(iter([k for k in keys if k]))
        min_key = min([k for k in keys if k])

        # 2. while we cannot add anymore, find all that are overlapping,
        # and add them to the list of records to be returned.  We update the
        # end position of the minimum key (min_key) to the maximum end so far
        # so we can return all overlapping variants.
        records = [[] for _ in self._iters]
        added = True
        while added:
            added = False
            # Go through each input iterator
            for i, _iter in enumerate(self._iters):
                # Get the first records
                rec = _iter.peek()
                if rec:
                    # Update the key if not defined
                    if not keys[i]:
                        keys[i] = self._sort_key(rec)
                    # Check if it overlaps
                    if self._overlap_f(min_key, keys[i]):
                        # Add it to the list, update the end, set added to
                        # true, and nullify the key
                        next_rec = next(_iter)
                        records[i].append(next_rec)
                        if min_key.end < keys[i].end:
                            min_key.end = keys[i].end
                        added = True
                        keys[i] = None

        return records


@unique
class AlleleOverlapType(Enum):
    """Enumeration for how to compare sets of alternate alleles.
    1. `Equality` requires that both sets are identical.
    2. `Intersects` requires that the two sets share at least one member.
    3. `Subset` requires that the second set is wholly contained in the first.
    """

    Equality = 0
    Intersects = 1
    Subset = 2

    @classmethod
    def compare_by(cls, overlap_type):
        """Gets the comparison method by type"""
        if overlap_type == AlleleOverlapType.Equality:
            return cls.equality
        elif overlap_type == AlleleOverlapType.Intersects:
            return cls.intersects
        else:
            return cls.subset

    @classmethod
    def equality(cls, base, other):
        """Returns true if the two lists have the same elements in order"""
        return base == other

    @classmethod
    def intersects(cls, base, other):
        """Returns true if the two lists intersect, or are both empty"""
        a = set(base)
        return any(i in a for i in other) or base == other

    @classmethod
    def subset(cls, base, other):
        """Returns true if the other list is a subset of the first list"""
        a = set(base)
        return all(i in a for i in other)


class LocatableByAlleleOverlapIterator(LocatableOverlapIterator):
    """
    Extends `LocatableOverlapIterator` to return only those loctables who have
    the same reference allele as a locatable from the **first** iterator, as
    well as the given relationship between the alternate alleles (i.e.
    equality, intersects, subset).
    """

    def __init__(
        self,
        iters,
        fasta_index=None,
        contigs=None,
        by_barcodes=True,
        overlap_type=AlleleOverlapType.Equality,
    ):
        """
        :param iters: the list of iterators.
        :param fasta_index: the path to the FASTA index for defining
        ordering across chromosomes.
        """
        super(LocatableByAlleleOverlapIterator, self).__init__(
            iters, fasta_index, contigs, by_barcodes
        )
        self._compare_alts = AlleleOverlapType.compare_by(overlap_type)

        self._list_of_items = None
        self._other_iters = None

    def __should_add(self, items, other):
        for item in items:
            if item.ref == other.ref and self._compare_alts(item.alts, other.alts):
                return True
        return False

    def __next__(self):
        if not self._list_of_items:
            # ensure that we have a locatable in the first iterator
            iters = super(LocatableByAlleleOverlapIterator, self).__next__()
            while not iters[0]:
                iters = super(LocatableByAlleleOverlapIterator, self).__next__()

            # partition the locatables within the first iterator
            _iter = iters[0]
            self._list_of_items = []
            while _iter:
                item = _iter[0]
                for _items in self._list_of_items:
                    if self.__should_add(_items, item):
                        _items.append(item)
                        item = None
                        break
                if item:
                    self._list_of_items.append([item])
                del _iter[0]

            self._other_iters = iters[1:]

        # get the next set of items from the first iter
        assert len(self._list_of_items) > 0
        _items = self._list_of_items[0]
        del self._list_of_items[0]

        # get matching items from the rest of the iters
        to_return = [_items]
        for _iter in self._other_iters:
            cur_items = []
            for item in _iter:
                if self.__should_add(_items, item):
                    cur_items.append(item)
            to_return.append(cur_items)

        return to_return


class _SortOrderEnforcingIterator(object):
    """An iterator that enforces a sort order."""

    def __init__(self, _iter, sort_order):
        self._iter = _iter
        self._sort_f = sort_order.sort_key()
        self._last_rec = None

    def __iter__(self):
        return self

    def next(self):
        """Gets the next element."""
        return self.__next__()

    def __next__(self):
        rec = next(self._iter)
        if self._last_rec:
            rec_key = self._sort_f(rec)
            last_rec_key = self._sort_f(self._last_rec)
            if rec_key < last_rec_key:
                raise Exception(
                    "Records out of order\n%s\n%s" % (str(self._last_rec), str(rec))
                )

        self._last_rec = rec
        return rec
