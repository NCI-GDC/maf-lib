"""Module with a maftool to view a MAF file"""
import sys

from enum import Enum, unique

from maflib.logger import Logger
from maflib.reader import MafReader
from maflib.scheme_factory import all_schemes, find_scheme
from maflib.writer import MafWriter
from maftools.subcommand import Subcommand


class View(Subcommand):
    """A maftool to view a MAF file"""

    print_every_n_records = 10000

    @classmethod
    def __add_arguments__(cls, subparser):
        """
        Add arguments to a subparser.
        """
        versions = list(set(s.version() for s in all_schemes()))
        annotations = [s.annotation_spec() for s in all_schemes()]
        subparser.add_argument('-i', '--input', dest='input',
                               required=True,
                               help='A MAF file.')
        subparser.add_argument('-v', '--version',
                               default=None,
                               help="Use the given version when validating "
                                    "rather than what's in the header.  "
                                    "Choices: %s" % ", ".join(versions))
        subparser.add_argument('-a', '--annotation',
                               type=str, default=None,
                               help="Use the given annotation specification "
                                    "when validating rather than what's in "
                                    "the header.  "
                                    "Choices: %s" % ", ".join(annotations))
        subparser.add_argument('-o', '--output', default=None,
                               help="The output file, otherwise output will be "
                                    "to standard output.")

    @classmethod
    def __get_description__(cls):
        """
        Gets the description to use for the sub-parser
        """
        return "View a MAF file"

    @classmethod
    def __validate_options(cls, options, scheme, logger):
        """Validate the command line options"""
        if scheme is not None:
            if options.version is None:
                logger.info("No version given, defaulting to version '%s' "
                            "based on -a/--annotation", scheme.version())
            if options.annotation is None:
                if scheme.is_basic():
                    logger.info("The scheme is assumed to be the basic scheme")
                else:
                    logger.info("No annotation given, defaulting to "
                                "annotation '%s'", scheme.annotation_spec())

    @classmethod
    def main(cls, options):
        """The main method."""
        logger = Logger.get_logger(cls.__name__)

        if options.version or options.annotation:
            scheme = find_scheme(version=options.version,
                                 annotation=options.annotation)
            if not scheme:
                tuples = ["\t%s %s" % (s.version(), s.annotation_spec()) for
                          s in all_schemes()]
                raise ValueError("Could not find a scheme with version '%s' "
                                 "and annotation '%s'.  Available schemes:\n%s"
                                 % (options.version, options.annotation,
                                    "\n".join(tuples)))
        else:
            scheme = None

        cls.__validate_options(options, scheme, logger)

        reader = MafReader.reader_from(
            path=options.input,
            validation_stringency=options.validation_stringency,
            scheme=scheme)

        if options.output:
            writer = MafWriter.writer_from(
                header=reader.header(),
                validation_stringency=options.validation_stringency,
                path=options.output,
            )
        else:
            writer = MafWriter.writer_from(
                header=reader.header(),
                validation_stringency=options.validation_stringency,
                handle=sys.stdout
            )

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
