"""This module contains an implementation of an variant overlapping iterator.

* MafOverlapIterator  allows for jointly iterating over multiple iterators and 
                      returning the set of variants that overlap between them.
"""

from maflib.util import PeekableIterator
from maflib.sorter import MafSorter
from maflib.sort_order import Coordinate


class MafOverlapIterator(object):
    """ An iterator over overlapping variants across multiple `MafRecord`s.
    One or more iterators should be given.  By default, the iterators are
    assumed to be sorted by coordinate order (see 
    `maflib.sort_order.Coordinate`), which will be verified during 
    iteration. Otherwise, the input will be sorted on the fly.  A list of 
    lists is returned each iteration, with one list of variants per input 
    iterators.  A list of variants per iterator is returned, since we have 
    multiple variants in one iterator overlapping a variant in the other.  
    For example, consider the following intervals representing variants on 
    one chromosome:
        iter#1: [1,10], [15,15], [30,40]
        iter#2: [5,25], [50,60]
    then we will return the following
        next#1: [ [[1,10], [15,15]], [[5,25]] ]
        next#2: [ [30,40], [] ]
        next#3: [ [], [[50, 60]] ]
    This scenario happens most frequently with MNPs, indels, and SVs.
    """

    def __init__(self,
                 iters,
                 assume_sorted=True,
                 fasta_index=None):

        self._sort_order = Coordinate(fasta_index=fasta_index)

        if assume_sorted:
            # Trust, but verify
            self._iters = [_SortOrderEnforcingIterator(_iter, self._sort_order)
                           for _iter in iters]
        else:
            # Do or do not, there is no try
            def generate_sorter(in_iter):
                """Generates an iterator over the records after sorting"""
                sorter = MafSorter(self._sort_order.name())
                for i in in_iter:
                    sorter += i
                return iter(sorter)
            self._iters = [generate_sorter(_iter) for _iter in iters]
        self._iters = [PeekableIterator(_iter) for _iter in self._iters]

        self._sort_f = self._sort_order.sort_key()

    def __iter__(self):
        return self

    def next(self):
        """Gets the next set of overlapping variants."""
        return self.__next__()

    def __to_sort_key(self, _iter):
        rec = _iter.peek()
        if rec is None:
            return None
        else:
            return self._sort_f(rec)

    def __next__(self):
        # 1. find the record with the earliest start.
        keys = [self.__to_sort_key(_iter) for _iter in self._iters]
        # check that we have at least one _iter that return a non-None value
        next(iter([k for k in keys if k]))
        min_key = min([k for k in keys if k])

        # 2. while we cannot add anymore, find all that are overlapping,
        # and add
        chromosome = min_key.chromosome
        start = min_key.start
        end = min_key.end
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
                        keys[i] = self._sort_f(rec)
                    # Check if it overlaps
                    # NB: since start was the minimum start, the current
                    # record's start cannot be less than the minimum start!
                    if chromosome == keys[i].chromosome \
                            and start <= keys[i].start <= end:
                        # Add it to the list, update the end, set added to
                        # true, and nullify the key
                        next_rec = next(_iter)
                        records[i].append(next_rec)
                        end = max(end, keys[i].end)
                        added = True
                        keys[i] = None

        return records


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
                raise Exception("Records out of order\n%s\n%s" %
                                (str(self._last_rec), str(rec)))

        self._last_rec = rec
        return rec
