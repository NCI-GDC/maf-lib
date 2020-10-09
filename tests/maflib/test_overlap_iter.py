import unittest

from maflib.column import MafColumnRecord
from maflib.overlap_iter import (
    AlleleOverlapType,
    LocatableByAlleleOverlapIterator,
    LocatableOverlapIterator,
    _SortOrderEnforcingIterator,
)
from maflib.record import MafRecord
from maflib.sort_order import Coordinate


class DummyRecord(MafRecord):
    def __init__(self, chromosome, start, end, tumor_barcode=None, normal_barcode=None):
        super(DummyRecord, self).__init__()
        self.add(MafColumnRecord("Chromosome", chromosome))
        self.add(MafColumnRecord("Start_Position", start))
        self.add(MafColumnRecord("End_Position", end))
        if tumor_barcode:
            self.add(MafColumnRecord("Tumor_Sample_Barcode", tumor_barcode))
        if normal_barcode:
            self.add(MafColumnRecord("Matched_Norm_Sample_Barcode", normal_barcode))


class TestSortOrderEnforcingIterator(unittest.TestCase):
    def test_ok(self):
        sort_order = Coordinate()

        records = [
            DummyRecord("A", 1, 2),
            DummyRecord("A", 1, 2),
            DummyRecord("B", 1, 2),
            DummyRecord("B", 2, 2),
            DummyRecord("C", 1, 2),
        ]

        items = [r for r in _SortOrderEnforcingIterator(iter(records), sort_order)]

        self.assertListEqual(items, records)
        for i, rec in enumerate(items):
            self.assertEqual(rec, records[i])

    def test_out_of_order(self):
        sort_order = Coordinate()

        records = [DummyRecord("A", 2, 2), DummyRecord("A", 1, 2)]

        with self.assertRaises(Exception) as context:
            items = [r for r in _SortOrderEnforcingIterator(iter(records), sort_order)]
        self.assertIn("out of order", str(context.exception))


class TestMafOverlapIterator(unittest.TestCase):

    RecordsNoOverlap = [
        DummyRecord("A", 1, 10),
        DummyRecord("A", 110, 200),
        DummyRecord("B", 1, 10),
        DummyRecord("B", 110, 200),
        DummyRecord("C", 1, 200),
    ]

    RecordsOverlapping = [
        DummyRecord("A", 1, 1),
        DummyRecord("A", 110, 200),
        DummyRecord("A", 150, 250),  # overlaps previous
        DummyRecord("B", 1, 10),
    ]

    RecordsSecondNoOverlap = [
        DummyRecord("A", 11, 109),
        DummyRecord("A", 201, 300),
        DummyRecord("B", 11, 109),
        DummyRecord("B", 201, 300),
        DummyRecord("C", 201, 300),
    ]

    RecordsSecondOverlappingFirst = [
        DummyRecord("B", 9, 9),  # overlaps third record in RecordsNoOverlap
        DummyRecord("D", 110, 200),
    ]

    def test_empty_iter(self):
        items = LocatableOverlapIterator([], by_barcodes=False)
        self.assertEqual(len([i for i in items]), 0)

    def test_single_iter_no_overlap(self):
        actual = TestMafOverlapIterator.RecordsNoOverlap
        items = LocatableOverlapIterator([iter(actual)], by_barcodes=False)

        n = 0
        for i, records in enumerate(items):
            self.assertEqual(len(records), 1)
            self.assertEqual(len(records[0]), 1)
            self.assertEqual(actual[i], records[0][0])
            n += 1
        self.assertEqual(n, len(actual))

    def test_single_iter_overlapping(self):
        actual = TestMafOverlapIterator.RecordsOverlapping
        items = LocatableOverlapIterator(
            [iter(TestMafOverlapIterator.RecordsOverlapping)], by_barcodes=False
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
        items = LocatableOverlapIterator(
            [iter(first), iter(second),], by_barcodes=False
        )

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
        items = LocatableOverlapIterator([iter(first), iter(second)], by_barcodes=False)

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
        items = LocatableOverlapIterator([iter(first), iter(second)], by_barcodes=False)
        expected_counts = [1, 1, 2, 1, 1, 1]

        n = first_i = second_i = 0
        for i, records in enumerate(items):
            self.assertEqual(len(records), 2)
            self.assertEqual(len(records[0]) + len(records[1]), expected_counts[n])
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

        items = LocatableOverlapIterator(
            [iter([left]), iter([right])], by_barcodes=False
        )

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

        items = LocatableOverlapIterator(
            [iter([left]), iter([right])], by_barcodes=False
        )

        # one record in one list
        records = next(items)
        self.assertEqual(len(records), 2)
        self.assertEqual(len(records[0]), 1)
        self.assertEqual(len(records[1]), 1)
        self.assertEqual(records[0][0], left)
        self.assertEqual(records[1][0], right)

        with self.assertRaises(StopIteration):
            next(items)

    def test_by_barcode_matching(self):
        left = TestMafOverlapIterator.RecordsNoOverlap
        right = TestMafOverlapIterator.RecordsNoOverlap

        # add the same tumor/normal barcodes to left and right
        left = [DummyRecord(r.chromosome, r.start, r.end, "T", "N") for r in left]
        right = [DummyRecord(r.chromosome, r.start, r.end, "T", "N") for r in right]

        # iterate by barcode
        items = LocatableOverlapIterator([iter(left), iter(right)], by_barcodes=True)

        n = 0
        for i, records in enumerate(items):
            self.assertEqual(len(records), 2)
            self.assertEqual(len(records[0]) + len(records[1]), 2)
            self.assertEqual(records[0][0], left[n])
            self.assertEqual(records[1][0], right[n])
            n += 1
        self.assertEqual(n, len(left))

        # ignore barcode
        items = LocatableOverlapIterator([iter(left), iter(right)], by_barcodes=False)

        n = 0
        for i, records in enumerate(items):
            self.assertEqual(len(records), 2)
            self.assertEqual(len(records[0]) + len(records[1]), 2)
            self.assertEqual(records[0][0], left[n])
            self.assertEqual(records[1][0], right[n])
            n += 1
        self.assertEqual(n, len(left))

    def test_by_barcode_mismatching(self):
        left = TestMafOverlapIterator.RecordsNoOverlap
        right = TestMafOverlapIterator.RecordsNoOverlap

        # add different tumor/normal barcodes to left and right
        left = [DummyRecord(r.chromosome, r.start, r.end, "A", "B") for r in left]
        right = [DummyRecord(r.chromosome, r.start, r.end, "B", "A") for r in right]

        # iterate by barcode
        items = LocatableOverlapIterator([iter(left), iter(right)], by_barcodes=True)

        n = 0
        for i, records in enumerate(items):
            self.assertEqual(len(records), 2)
            if n < len(left):
                self.assertEqual(len(records[0]), 1)
                self.assertEqual(len(records[1]), 0)
                self.assertEqual(records[0][0], left[n])
            else:
                self.assertEqual(len(records[0]), 0)
                self.assertEqual(len(records[1]), 1)
                self.assertEqual(records[1][0], right[n - len(left)])
            n += 1
        self.assertEqual(n, len(left) + len(right))

        # ignore barcode
        items = LocatableOverlapIterator([iter(left), iter(right)], by_barcodes=False)

        n = 0
        for i, records in enumerate(items):
            self.assertEqual(len(records), 2)
            self.assertEqual(len(records[0]) + len(records[1]), 2)
            self.assertEqual(records[0][0], left[n])
            self.assertEqual(records[1][0], right[n])
            n += 1
        self.assertEqual(n, len(left))


class TestAlleleOverlapType(unittest.TestCase):
    def test_equality(self):
        f = AlleleOverlapType.equality
        self.assertTrue(f([], []))
        self.assertTrue(f([1], [1]))
        self.assertTrue(f([1, 2], [1, 2]))

        self.assertFalse(f([1], [2]))
        self.assertFalse(f([1, 2], [2, 1]))
        self.assertFalse(f([], [2]))
        self.assertFalse(f([1], []))

    def test_intersects(self):
        f = AlleleOverlapType.intersects
        self.assertTrue(f([], []))
        self.assertTrue(f([1], [1]))
        self.assertTrue(f([1, 2], [1, 2]))
        self.assertTrue(f([1, 2], [2, 1]))
        self.assertTrue(f([1, 2, 3], [3]))

        self.assertFalse(f([1], [2]))
        self.assertFalse(f([], [2]))
        self.assertFalse(f([1], []))
        self.assertFalse(f([1, 2, 3], []))
        self.assertFalse(f([], [1, 2, 3]))

    def test_subset(self):
        f = AlleleOverlapType.subset
        self.assertTrue(f([], []))
        self.assertTrue(f([1], [1]))
        self.assertTrue(f([1], []))
        self.assertTrue(f([1, 2], [1, 2]))
        self.assertTrue(f([1, 2, 3], []))
        self.assertTrue(f([1, 2, 3], [3]))
        self.assertTrue(f([1, 2, 3], [1, 3]))
        self.assertTrue(f([1, 2, 3], [1, 2, 3]))
        self.assertTrue(f([1, 2], [2, 1]))

        self.assertFalse(f([1], [2]))
        self.assertFalse(f([], [2]))
        self.assertFalse(f([], [1, 2, 3]))
        self.assertFalse(f([1, 2, 3], [1, 2, 3, 4]))


class DummyRecordWithAllele(MafRecord):
    def __init__(self, chromosome, start, end, ref="A", alts=None):
        super(DummyRecordWithAllele, self).__init__()
        self.add(MafColumnRecord("Chromosome", chromosome))
        self.add(MafColumnRecord("Start_Position", start))
        self.add(MafColumnRecord("End_Position", end))
        self.add(MafColumnRecord("Reference_Allele", ref))
        self._alts = alts if alts else []

    @property
    def alts(self):
        return self._alts


class TestLocatableByAlleleOverlapIterator(unittest.TestCase):
    def test_multiple_loci(self):
        for by_barcodes in [True, False]:
            for overlap_type in AlleleOverlapType:
                actual = [
                    DummyRecordWithAllele("A", 1, 10),
                    DummyRecordWithAllele("A", 110, 200),
                    DummyRecordWithAllele("B", 1, 10),
                    DummyRecordWithAllele("B", 110, 200),
                    DummyRecordWithAllele("C", 1, 200),
                ]

                items = LocatableByAlleleOverlapIterator(
                    iters=[iter(actual)],
                    overlap_type=overlap_type,
                    by_barcodes=by_barcodes,
                )
                n = 0
                for i, records in enumerate(items):
                    self.assertEqual(len(records), 1)
                    self.assertEqual(len(records[0]), 1)
                    self.assertEqual(actual[i], records[0][0])
                    n += 1
                self.assertEqual(n, len(actual))

    def test_single_iter_overlapping(self):
        for overlap_type in AlleleOverlapType:
            for alts in [[], ["A"], ["A", "C"]]:
                actual = [
                    DummyRecordWithAllele("A", 1, 10, alts=alts),
                    DummyRecordWithAllele("A", 5, 20, alts=alts),
                ]

                items = LocatableByAlleleOverlapIterator(
                    iters=[iter(actual)], overlap_type=overlap_type, by_barcodes=False
                )

                records = next(items)
                self.assertEqual(len(records), 1)
                self.assertEqual(len(records[0]), 2)
                self.assertEqual(records[0][0], actual[0])
                self.assertEqual(records[0][1], actual[1])

    def test_diff_ref_alleles(self):
        for overlap_type in AlleleOverlapType:
            actual = [
                DummyRecordWithAllele("A", 1, 10, "A"),
                DummyRecordWithAllele("A", 1, 10, "C"),
            ]

            items = LocatableByAlleleOverlapIterator(
                iters=[iter(actual)], overlap_type=overlap_type, by_barcodes=False
            )
            n = 0
            for i, records in enumerate(items):
                self.assertEqual(len(records), 1)
                self.assertEqual(len(records[0]), 1)
                self.assertEqual(actual[i], records[0][0])
                n += 1
            self.assertEqual(n, len(actual))

    def test_diff_alt_alleles(self):
        for overlap_type in AlleleOverlapType:
            actual = [
                DummyRecordWithAllele("A", 1, 10, "A", ["A"]),
                DummyRecordWithAllele("A", 1, 10, "A", ["C"]),
            ]

            items = LocatableByAlleleOverlapIterator(
                iters=[iter(actual)], overlap_type=overlap_type, by_barcodes=False
            )
            n = 0
            for i, records in enumerate(items):
                self.assertEqual(len(records), 1)
                self.assertEqual(len(records[0]), 1)
                self.assertEqual(actual[i], records[0][0])
                n += 1
            self.assertEqual(n, len(actual))

    def test_diff_alt_alleles_multiple_iters(self):
        base = DummyRecordWithAllele("A", 1, 10, "A", ["A", "C"])
        equality = DummyRecordWithAllele("A", 1, 10, "A", ["A", "C"])
        intersects = DummyRecordWithAllele("A", 1, 10, "A", ["C", "D"])
        subset = DummyRecordWithAllele("A", 1, 10, "A", ["C"])
        disjoint = DummyRecordWithAllele("A", 1, 10, "A", ["D"])

        for overlap_type in AlleleOverlapType:
            iters = [
                iter([base]),
                iter([equality]),
                iter([intersects]),
                iter([subset]),
                iter([disjoint]),
            ]

            items = LocatableByAlleleOverlapIterator(
                iters=iters, overlap_type=overlap_type, by_barcodes=False
            )

            records = next(items)
            if overlap_type == AlleleOverlapType.Equality:
                self.assertEqual(len(records), 5)
                self.assertEqual(len(records[0]), 1)
                self.assertEqual(len(records[1]), 1)
                self.assertEqual(len(records[2]), 0)
                self.assertEqual(len(records[3]), 0)
                self.assertEqual(len(records[4]), 0)
                self.assertEqual(records[0][0], base)
                self.assertEqual(records[1][0], equality)
            elif overlap_type == AlleleOverlapType.Intersects:
                self.assertEqual(len(records), 5)
                self.assertEqual(len(records[0]), 1)
                self.assertEqual(len(records[1]), 1)
                self.assertEqual(len(records[2]), 1)
                self.assertEqual(len(records[3]), 1)
                self.assertEqual(len(records[4]), 0)
                self.assertEqual(records[0][0], base)
                self.assertEqual(records[1][0], equality)
                self.assertEqual(records[2][0], intersects)
                self.assertEqual(records[3][0], subset)
            else:  # Subset
                self.assertEqual(len(records), 5)
                self.assertEqual(len(records[0]), 1)
                self.assertEqual(len(records[1]), 1)
                self.assertEqual(len(records[2]), 0)
                self.assertEqual(len(records[3]), 1)
                self.assertEqual(len(records[4]), 0)
                self.assertEqual(records[0][0], base)
                self.assertEqual(records[1][0], equality)
                self.assertEqual(records[3][0], subset)

            with self.assertRaises(StopIteration):
                next(items)

    def test_non_overlapping_other(self):
        for overlap_type in AlleleOverlapType:
            base = DummyRecordWithAllele("A", 100, 110, "A", ["A"])
            other = DummyRecordWithAllele("A", 1, 10, "A", ["A"])

            items = LocatableByAlleleOverlapIterator(
                iters=[iter([base]), iter([other])],
                overlap_type=overlap_type,
                by_barcodes=False,
            )

            records = next(items)
            self.assertEqual(len(records), 2)
            self.assertEqual(len(records[0]), 1)
            self.assertEqual(len(records[1]), 0)
            self.assertEqual(records[0][0], base)

            with self.assertRaises(StopIteration):
                next(items)
