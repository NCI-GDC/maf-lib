import unittest

from maflib.overlap_iter import MafOverlapIterator, _SortOrderEnforcingIterator
from maflib.sort_order import Coordinate
from maflib.record import MafRecord
from maflib.column import MafColumnRecord


class DummyRecord(MafRecord):
    def __init__(self, chromosome, start, end):
        super(DummyRecord, self).__init__()
        self.add(MafColumnRecord("Chromosome", chromosome))
        self.add(MafColumnRecord("Start_Position", start))
        self.add(MafColumnRecord("End_Position", end))


class TestSortOrderEnforcingIterator(unittest.TestCase):

    def test_ok(self):
        sort_order = Coordinate()

        records = [
            DummyRecord("A", 1, 2),
            DummyRecord("A", 1, 2),
            DummyRecord("B", 1, 2),
            DummyRecord("B", 2, 2),
            DummyRecord("C", 1, 2)
        ]

        items = [r for r in
                 _SortOrderEnforcingIterator(iter(records), sort_order)
                 ]

        self.assertListEqual(items, records)
        for i, rec in enumerate(items):
            self.assertEqual(rec, records[i])

    def test_out_of_order(self):
        sort_order = Coordinate()

        records = [
            DummyRecord("A", 2, 2),
            DummyRecord("A", 1, 2)
        ]

        with self.assertRaises(Exception) as context:
            items = [r for r in
                     _SortOrderEnforcingIterator(iter(records),  sort_order)
                     ]
        self.assertIn("out of order", str(context.exception))


class TestMafOverlapIterator(unittest.TestCase):

    RecordsNoOverlap = [
        DummyRecord("A", 1, 10),
        DummyRecord("A", 110, 200),
        DummyRecord("B", 1, 10),
        DummyRecord("B", 110, 200),
        DummyRecord("C", 1, 200)
    ]

    RecordsOverlapping = [
        DummyRecord("A", 1, 1),
        DummyRecord("A", 110, 200),
        DummyRecord("A", 150, 250),  # overlaps previous
        DummyRecord("B", 1, 10)
    ]

    RecordsSecondNoOverlap = [
        DummyRecord("A", 11, 109),
        DummyRecord("A", 201, 300),
        DummyRecord("B", 11, 109),
        DummyRecord("B", 201, 300),
        DummyRecord("C", 201, 300)
    ]

    RecordsSecondOverlappingFirst = [
        DummyRecord("B", 9, 9),  # overlaps third record in RecordsNoOverlap
        DummyRecord("D", 110, 200)
    ]

    def test_empty_iter(self):
        items = MafOverlapIterator([])
        self.assertEqual(len([i for i in items]), 0)

    def test_single_iter_no_overlap(self):
        actual = TestMafOverlapIterator.RecordsNoOverlap
        items = MafOverlapIterator([iter(actual)])

        n = 0
        for i, records in enumerate(items):
            self.assertEqual(len(records), 1)
            self.assertEqual(len(records[0]), 1)
            self.assertEqual(actual[i], records[0][0])
            n += 1
        self.assertEqual(n, len(actual))

    def test_single_iter_no_overlap_unsorted(self):
        actual = TestMafOverlapIterator.RecordsNoOverlap
        items = MafOverlapIterator([iter(reversed(actual))],
                                   assume_sorted=False)

        n = 0
        for i, records in enumerate(items):
            self.assertEqual(len(records), 1)
            self.assertEqual(len(records[0]), 1)
            # NB: must test as strings since we always spill to disk when
            # sorting
            self.assertEqual(str(actual[i]), str(records[0][0]))
            n += 1
        self.assertEqual(n, len(actual))

    def test_single_iter_overlapping(self):
        actual = TestMafOverlapIterator.RecordsOverlapping
        items = MafOverlapIterator(
            [iter(TestMafOverlapIterator.RecordsOverlapping)]
        )

        # one record in one list
        records = next(items)
        self.assertEqual(len(records), 1)
        self.assertEqual(len(records[0]), 1)
        self.assertEqual(records[0][0], actual[0])

        # two records in one list
        records = next(items)
        self.assertEqual(len(records), 1)
        self.assertEqual(len(records[0]), 2)
        self.assertEqual(records[0][0], actual[1])
        self.assertEqual(records[0][1], actual[2])

        # one record in one list
        records = next(items)
        self.assertEqual(len(records), 1)
        self.assertEqual(len(records[0]), 1)
        self.assertEqual(records[0][0], actual[3])

        with self.assertRaises(StopIteration):
            next(items)

    def test_two_iter_no_overlap(self):
        first = TestMafOverlapIterator.RecordsNoOverlap
        second = TestMafOverlapIterator.RecordsSecondNoOverlap
        items = MafOverlapIterator([
            iter(first), iter(second)
        ])

        n = first_i = second_i = 0
        for i, records in enumerate(items):
            self.assertEqual(len(records), 2)
            self.assertEqual(len(records[0]) + len(records[1]), 1)
            if len(records[0]) > 0:
                self.assertEqual(records[0][0], first[first_i])
                first_i += 1
            else:
                self.assertEqual(records[1][0], second[second_i])
                second_i += 1
            n += 1
        self.assertEqual(n, len(first) + len(second))
        self.assertEqual(first_i, len(first))
        self.assertEqual(second_i, len(second))

    def test_two_iter_same(self):
        first = TestMafOverlapIterator.RecordsNoOverlap
        second = TestMafOverlapIterator.RecordsNoOverlap
        items = MafOverlapIterator([
            iter(first), iter(second)
        ])

        n = 0
        for i, records in enumerate(items):
            self.assertEqual(len(records), 2)
            self.assertEqual(len(records[0]) + len(records[1]), 2)
            self.assertEqual(records[0][0], first[n])
            self.assertEqual(records[1][0], second[n])
            n += 1
        self.assertEqual(n, len(first))

    def test_two_iter_second_overlaps_first(self):
        first = TestMafOverlapIterator.RecordsNoOverlap
        second = TestMafOverlapIterator.RecordsSecondOverlappingFirst
        items = MafOverlapIterator([
            iter(first), iter(second)
        ])
        expected_counts = [1, 1, 2, 1, 1, 1]

        n = first_i = second_i = 0
        for i, records in enumerate(items):
            self.assertEqual(len(records), 2)
            self.assertEqual(len(records[0]) + len(records[1]),
                             expected_counts[n])
            if len(records[0]) > 0:
                self.assertEqual(records[0][0], first[first_i])
                first_i += 1
            if len(records[1]) > 0:
                self.assertEqual(records[1][0], second[second_i])
                second_i += 1
            n += 1
        self.assertEqual(first_i + second_i, len(first) + len(second))
        self.assertEqual(first_i, len(first))
        self.assertEqual(second_i, len(second))

    def test_record_contained(self):
        # tests if right is fully contained in left
        left = DummyRecord("A", 11, 109)
        right = DummyRecord("A", 12, 108)

        items = MafOverlapIterator([
            iter([left]), iter([right])
        ])

        # one record in one list
        records = next(items)
        self.assertEqual(len(records), 2)
        self.assertEqual(len(records[0]), 1)
        self.assertEqual(len(records[1]), 1)
        self.assertEqual(records[0][0], left)
        self.assertEqual(records[1][0], right)

        with self.assertRaises(StopIteration):
            next(items)

    def test_record_overlap(self):
        # tests if right is fully contained in left
        left = DummyRecord("A", 11, 109)
        right = DummyRecord("A", 100, 200)

        items = MafOverlapIterator([
            iter([left]), iter([right])
        ])

        # one record in one list
        records = next(items)
        self.assertEqual(len(records), 2)
        self.assertEqual(len(records[0]), 1)
        self.assertEqual(len(records[1]), 1)
        self.assertEqual(records[0][0], left)
        self.assertEqual(records[1][0], right)

        with self.assertRaises(StopIteration):
            next(items)
