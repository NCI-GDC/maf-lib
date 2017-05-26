import os
import unittest
from collections import OrderedDict

from maflib.column_types import StringColumn, IntegerColumn
from maflib.schemes import MafScheme
from maflib.sort_order import BarcodeAndCoordinate
from maflib.sorter import MafSorterCodec, Sorter, MafSorter
from maflib.tests.testutils import tmp_file


class DummyScheme(MafScheme):
    @classmethod
    def version(cls):
        return "dummy-version"

    @classmethod
    def annotation_spec(cls):
        return "dummy-annotation"

    @classmethod
    def __column_dict__(cls):
        return OrderedDict([("Tumor_Sample_Barcode", StringColumn),
                            ("Matched_Norm_Sample_Barcode", StringColumn),
                            ("Chromosome", StringColumn),
                            ("Start_Position", IntegerColumn),
                            ("End_Position", IntegerColumn)])


class DummyRecord(object):
    def __init__(self, tumor_barcode, normal_barcode, chr, start, end):
        self._dict = OrderedDict()
        self._dict["Tumor_Sample_Barcode"] = tumor_barcode
        self._dict["Matched_Norm_Sample_Barcode"] = normal_barcode
        self._dict["Chromosome"] = chr
        self._dict["Start_Position"] = start
        self._dict["End_Position"] = end

    def value(self, key):
        return self._dict[key]

    def keys(self):
        return list(self._dict.keys())

    def __str__(self):
        return "\t".join([str(s) for s in self._dict.values()])


class TestMafSorterCodec(unittest.TestCase):

    def test_round_trip_no_column_names(self):
        codec = MafSorterCodec()
        original = DummyRecord("A", "B", "C", 1, 2)
        bytes = codec.encode(original)
        result = codec.decode(bytes, 0, len(bytes))
        self.assertEqual(str(result), str(original))

    def test_round_trip_column_names(self):
        codec = MafSorterCodec(column_names=DummyScheme().column_names())
        original = DummyRecord("A", "B", "C", 1, 2)
        bytes = codec.encode(original)
        result = codec.decode(bytes, 0, len(bytes))
        self.assertEqual(str(result), str(original))

    def test_round_trip_scheme(self):
        codec = MafSorterCodec(scheme=DummyScheme())
        original = DummyRecord("A", "B", "C", 1, 2)
        bytes = codec.encode(original)
        result = codec.decode(bytes, 0, len(bytes))
        self.assertEqual(str(result), str(original))


class TestSorter(unittest.TestCase):

    def codec(self): return MafSorterCodec(scheme=DummyScheme())

    def test_empty(self):
        sorter = Sorter(100, self.codec(), BarcodeAndCoordinate().sort_key())
        records = [r for r in sorter]
        sorter.close()
        self.assertEqual(len(records), 0)

    def test_less_than_max_in_memory(self):
        max_objects_in_ram = 100
        num_records = max_objects_in_ram - 1
        sorter = Sorter(max_objects_in_ram, self.codec(),
                        BarcodeAndCoordinate().sort_key(),
                        always_spill=False)

        # add them in reverse order
        for i in range(num_records):
            record = DummyRecord("A", "B", "C", 1, num_records-i-1)
            sorter += record
        records = [r for r in sorter]
        sorter.close()
        self.assertEqual(len(records), num_records)

        for i in range(num_records):
            record = records[i]
            self.assertEqual(record.value("End_Position"), i)

    def test_spilling_to_disk(self):
        max_objects_in_ram = 100
        num_records = max_objects_in_ram * 10
        sorter = Sorter(max_objects_in_ram, self.codec(),
                        BarcodeAndCoordinate().sort_key(),
                        always_spill=True)

        # add them in reverse order
        for i in range(num_records):
            record = DummyRecord("A", "B", "C", 1, num_records-i-1)
            sorter += record
        records = [r for r in sorter]
        sorter.close()
        self.assertEqual(len(records), num_records)

        for i in range(num_records):
            record = records[i]
            self.assertEqual(record.value("End_Position"), i)


class TestMafSorter(unittest.TestCase):

    def __test_sorter(self, sorter, chromosome="C", with_scheme=False):
        """
        :param sorter: the sorter to use
        :param chromosome: the chromosome value to use for all generated 
        records 
        :param with_scheme: true if a scheme was used with the sorter, false
         otherwise.  If no scheme was used, compares the value as strings.
        """

        num_records = sorter._max_objects_in_ram - 1

        # add them in reverse order
        records = []
        for i in range(num_records):
            record = DummyRecord("A", "B", chromosome, 1, num_records - i - 1)
            records.append(record)
            sorter += record
        # sort by end position here
        records = sorted(records, key=lambda r: r.value("End_Position"))

        # read them back in
        sorted_records = [r for r in sorter]
        sorter.close()
        self.assertEqual(len(sorted_records), num_records)

        for i in range(num_records):
            record = sorted_records[i]
            if with_scheme:
                self.assertEqual(record.value("End_Position"),
                                 records[i].value("End_Position"))
            else:
                self.assertEqual(record.value("End_Position"),
                                 str(records[i].value( "End_Position")))

    def test_sorter_default(self):
        sorter = MafSorter(sort_order_name=BarcodeAndCoordinate.name(),
                           max_objects_in_ram=100)
        self.__test_sorter(sorter=sorter)

    def test_sorter_with_scheme(self):
        scheme = DummyScheme()
        sorter = MafSorter(sort_order_name=BarcodeAndCoordinate.name(),
                           scheme=scheme,
                           max_objects_in_ram=100)
        self.__test_sorter(sorter=sorter, with_scheme=True)

    def test_sorter_with_sort_order_args(self):
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

        sorter = MafSorter(sort_order_name=BarcodeAndCoordinate.name(),
                           max_objects_in_ram=100,
                           fasta_index=fn)

        self.__test_sorter(sorter=sorter, chromosome="chr5")

        with self.assertRaises(ValueError):
            self.__test_sorter(sorter=sorter, chromosome="1")

        fd.close()
        os.remove(fn)

