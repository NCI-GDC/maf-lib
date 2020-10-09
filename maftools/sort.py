"""Module with a maftool to sort a MAF file"""

from enum import Enum, unique

from maflib.logger import Logger
from maflib.reader import MafReader
from maflib.sort_order import SortOrder, BarcodesAndCoordinate
from maflib.sorter import MafSorter
from maftools.subcommand import Subcommand
from maftools.util import writer_from_reader


class Sort(Subcommand):
    """A maftool to view a MAF file"""

    print_every_n_records = 10000

    @classmethod
    def __add_arguments__(cls, subparser):
        """
        Add arguments to a subparser.
        """
        sort_orders = [c.name() for c in SortOrder.all()]
        subparser.add_argument('-i', '--input', dest='input',
                               required=True,
                               help='A MAF file.')
        subparser.add_argument('-o', '--output', default=None,
                               help="The output file, otherwise output will be"
                                    " to standard output.")
        subparser.add_argument('-s', '--sort-order',
                               default=BarcodesAndCoordinate.name(),
                               choices=sort_orders,
                               help="The sort order to choose.  "
                                    "Choices: %s" % ", ".join(sort_orders))
        subparser.add_argument('-f', '--fasta-index', default=None,
                               help="Use the FASTA index (fai) to order "
                                    "genomic coordinates.")

    @classmethod
    def __get_description__(cls):
        """
        Gets the description to use for the sub-parser
        """
        return "View a MAF file"

    @classmethod
    def __main__(cls, options):
        """The main method."""
        logger = Logger.get_logger(cls.__name__)

        reader = MafReader.reader_from(
            path=options.input,
            validation_stringency=options.validation_stringency,
            scheme=options.scheme)

        writer = writer_from_reader(reader=reader, options=options)

        sorter = MafSorter(
            max_objects_in_ram=100000,
            sort_order_name=options.sort_order,
            scheme=writer.header().scheme(),
            fasta_index=options.fasta_index
        )

        # add the records to the sorter
        n = 0
        for record in reader:
            sorter += record
            n = n + 1
            if options.output and n % Sort.print_every_n_records == 0:
                logger.info("Sorted %d records" % n)
        if options.output and (n == 0 or n % Sort.print_every_n_records != 0):
            logger.info("Sorted %d records" % n)

        # read from the sorter
        n = 0
        for record in sorter:
            writer += record
            n = n + 1
            if options.output and n % Sort.print_every_n_records == 0:
                logger.info("Wrote %d records" % n)
        if options.output and (n == 0 or n % Sort.print_every_n_records != 0):
            logger.info("Wrote %d records" % n)
            
        sorter.close()
        reader.close()
        writer.close()


@unique
class Mode(Enum):
    """A simple enumeration for the validation report mode"""
    Summary = 1
    Verbose = 2
