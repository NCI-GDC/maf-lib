import os
import unittest

from maflib.sort_order import *
from maflib.tests.testutils import tmp_file


class TestSortOrder(unittest.TestCase):
    def test_find(self):
        self.assertEqual(SortOrder.find(BarcodeAndCoordinate.name()),
                         BarcodeAndCoordinate)
        with self.assertRaises(ValueError):
            SortOrder.find("no-name")


class TestSortOrderKey(unittest.TestCase):

    class Comparable(SortOrderKey):
        def __init__(self, value):
            self.value = value

        def __cmp__(self, other):
            return self.compare(self.value, other.value)

    def test_compare(self):
        self.assertEqual(SortOrderKey.compare(1, 2), -1)
        self.assertEqual(SortOrderKey.compare(3, 2), 1)
        self.assertEqual(SortOrderKey.compare(2, 2), 0)

        lower = TestSortOrderKey.Comparable(1)
        higher = TestSortOrderKey.Comparable(2)
        self.assertEqual(SortOrderKey.compare(lower, higher), -1)
        self.assertEqual(SortOrderKey.compare(higher, lower), 1)
        self.assertEqual(SortOrderKey.compare(lower, lower), 0)

class TestBarcodeAndCoordinateKey(unittest.TestCase):

    TestSortOrder = BarcodeAndCoordinate()

    class DummyRecord(object):
        def __init__(self, tumor_barcode, normal_barcode, chr, start, end):
            self._dict = dict()
            self._dict["Tumor_Sample_Barcode"] = tumor_barcode
            self._dict["Matched_Norm_Sample_Barcode"] = normal_barcode
            self._dict["Chromosome"] = chr
            self._dict["Start_Position"] = start
            self._dict["End_Position"] = end

        def value(self, key):
            return self._dict[key]

    def __test_diff(self, r1, r2, sort_key=None):
        if not sort_key:
            sort_key = TestBarcodeAndCoordinateKey.TestSortOrder.sort_key()
        k1 = sort_key(r1)
        k2 = sort_key(r2)

        self.assertLess(k1, k2)
        self.assertEqual(k1, k1)
        self.assertEqual(k1 == k1, True)
        self.assertGreater(k2, k1)

    def test_name(self):
        self.assertEqual(TestBarcodeAndCoordinateKey.TestSortOrder.name(),
                         "BarcodesAndCoordinate")

    def test_diff_tumor_barcode(self):
        r1 = TestBarcodeAndCoordinateKey.DummyRecord("A", "B", "C", 1, 2)
        r2 = TestBarcodeAndCoordinateKey.DummyRecord("B", "B", "C", 1, 2)
        self.__test_diff(r1, r2)

    def test_diff_normal_barcode(self):
        r1 = TestBarcodeAndCoordinateKey.DummyRecord("A", "B", "C", 1, 2)
        r2 = TestBarcodeAndCoordinateKey.DummyRecord("A", "C", "C", 1, 2)
        self.__test_diff(r1, r2)

    def test_diff_chromosome(self):
        r1 = TestBarcodeAndCoordinateKey.DummyRecord("A", "B", "C", 1, 2)
        r2 = TestBarcodeAndCoordinateKey.DummyRecord("A", "B", "D", 1, 2)
        self.__test_diff(r1, r2)

    def test_diff_start(self):
        r1 = TestBarcodeAndCoordinateKey.DummyRecord("A", "B", "C", 1, 2)
        r2 = TestBarcodeAndCoordinateKey.DummyRecord("A", "B", "C", 2, 2)
        self.__test_diff(r1, r2)

    def test_diff_end(self):
        r1 = TestBarcodeAndCoordinateKey.DummyRecord("A", "B", "C", 1, 2)
        r2 = TestBarcodeAndCoordinateKey.DummyRecord("A", "B", "C", 1, 3)
        self.__test_diff(r1, r2)

    def test_with_contigs(self):
        lines = ["chr1\t248956422\t112\t70\t71"
                 "chr2\t242193529\t252513167\t70\t71",
                 "chr3\t198295559\t498166716\t70\t71",
                 "chr4\t190214555\t699295181\t70\t71",
                 "chr5\t181538259\t892227221\t70\t71",
                 "chr6\t170805979\t1076358996\t70\t71",
                 "chr7\t159345973\t1249605173\t70\t71",
                 "chr8\t145138636\t1411227630\t70\t71",
                 "chr9\t138394717\t1558439788\t70\t71",
                 "chr10\t133797422\t1698811686\t70\t71"
                 ]
        fd, fn = tmp_file(lines=lines)

        sort_order = BarcodeAndCoordinate(fasta_index=fn)
        sort_key = sort_order.sort_key()

        r1 = TestBarcodeAndCoordinateKey.DummyRecord("A", "B", "chr1", 1, 2)
        r2 = TestBarcodeAndCoordinateKey.DummyRecord("A", "B", "chr10", 1, 3)
        r3 = TestBarcodeAndCoordinateKey.DummyRecord("A", "B", "no-chr", 1, 3)

        # both have contigs defined
        self.__test_diff(r1, r2, sort_key=sort_key)

        # contig undefined
        with self.assertRaises(ValueError):
            k3 = sort_key(r3)

        fd.close()
        os.remove(fn)