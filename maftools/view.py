"""Module with a maftool to view a MAF file"""

from enum import Enum, unique

from maflib.logger import Logger
from maflib.reader import MafReader
from maftools.subcommand import Subcommand
from maftools.util import writer_from_reader


class View(Subcommand):
    """A maftool to view a MAF file"""

    print_every_n_records = 10000

    @classmethod
    def __add_arguments__(cls, subparser):
        """
        Add arguments to a subparser.
        """
        subparser.add_argument('-i', '--input', dest='input',
                               required=True,
                               help='A MAF file.')
        subparser.add_argument('-o', '--output', default=None,
                               help="The output file, otherwise output will be"
                                    " to standard output.")

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

        n = 0
        for record in reader:
            writer += record
            n = n + 1
            if options.output and n % View.print_every_n_records == 0:
                logger.info("Processed %d records" % n)
        if options.output and (n == 0 or n % View.print_every_n_records != 0):
            logger.info("Processed %d records" % n)

        reader.close()
        writer.close()


@unique
class Mode(Enum):
    """A simple enumeration for the validation report mode"""
    Summary = 1
    Verbose = 2
