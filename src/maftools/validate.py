"""Module with a maftool to validate a MAF file"""
import sys
from argparse import ArgumentTypeError

from enum import Enum, unique

from maflib.logger import Logger
from maflib.reader import MafReader
from maflib.scheme_factory import all_schemes, find_scheme
from maflib.validation import ValidationStringency
from maftools.subcommand import Subcommand
from maftools.util import StoreEnumAction


class ValidationErrors(object):
    """Container for storing and writing validation errors.
    
    Validation errors can be added via the ``extend`` method.  The ``write`` 
    method writes the errors until the maximum number of errors has been
    written. It also clears the errors after writing to reduce memory.    
    """
    def __init__(self, max_errors=sys.maxsize):
        self.num = 0
        self.errors = list()
        self.max_errors = max_errors

    def extend(self, errors):
        """ Copies the given errors. """
        reader_errors = errors
        self.num += len(reader_errors)
        self.errors.extend(reader_errors)

    def write(self, handle):
        """Writes the current list of errors to the handler.  If too many 
        errors have been written across all calls to ``write``, returns False, 
        otherwise True."""
        result = True
        num_errors_to_print = len(self.errors)
        for i, error in enumerate(self.errors):
            if self.max_errors <= self.num - num_errors_to_print + i:
                result = False
                break
            handle.write(str(error) + "\n")
        self.errors = list()
        return result


class Validate(Subcommand):
    """A maftool to validate a MAF file"""

    print_every_n_records = 10000

    @staticmethod
    def type_max_errors(value):
        """Custom type for parsing the -M/--max-errors option"""
        max_errors = int(value)
        if max_errors <= 0:
            raise ArgumentTypeError("must be greater than zero when specified")
        return max_errors

    @classmethod
    def __add_arguments__(cls, subparser):
        """
        Add arguments to a subparser.
        """
        versions = list(set(s.version() for s in all_schemes()))
        annotations = [s.annotation_spec() for s in all_schemes()]
        subparser.add_argument('-i', '--input', dest='input', action='append',
                               required=True,
                               help='One or more MAF files.')
        subparser.add_argument('-v', '--version',
                               default=None,
                               choices=versions,
                               help="Use the given version when validating "
                                    "rather than what's in the header.  "
                                    "Choices: %s" % ", ".join(versions))
        subparser.add_argument('-a', '--annotation',
                               type=str, default=None,
                               choices=annotations,
                               help="Use the given annotation specification "
                                    "when validating rather than what's in "
                                    "the header.  "
                                    "Choices: %s" % ", ".join(annotations))
        subparser.add_argument('-m', '--mode',
                               action=StoreEnumAction, type=Mode,
                               default=Mode.Verbose,
                               help="The mode of output.")
        subparser.add_argument('-M', '--max-errors',
                               type=Validate.type_max_errors, default=None,
                               help="The maximum number of errors before "
                                    "stopping.")
        subparser.add_argument('-o', '--output', default=None,
                               help="The output file, otherwise output will be "
                                    "to standard output.")

    @classmethod
    def __get_description__(cls):
        """
        Gets the description to use for the sub-parser
        """
        return "Validate a MAF file"

    @classmethod
    def __process_errors(cls, options, reader, logger, handle, errors):
        """Adds the current set of errors from the reader to the error class 
        and clears the errors in the reader.  If the mode is verbose, writes 
        the errors to the handler, stopping when the specified maximum has 
        been reached.  Returns true if too many errors have been found, 
        false otherwise."""

        # Transfer errors from reader to errors
        errors.extend(reader.validation_errors)
        reader.validation_errors = list()

        # Write the errors out if we are in Verbose mode
        if options.mode == Mode.Verbose and not errors.write(handle):
            logger.warning("Maximum number of errors encountered")
            return True
        elif options.mode == Mode.Summary and len(errors.errors) >= \
                errors.max_errors:
            logger.warning("Maximum number of errors encountered")
            return True

        return False

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
    def __print_report(cls, options, errors, handle):
        """Prints out the validation report"""

        if not errors.errors and errors.num == 0:
            handle.write("No errors found\n")
        elif options.mode == Mode.Summary:
            errors = errors.errors
            types = {error.tpe: sum(e.tpe == error.tpe for e in errors)
                     for error in errors}
            handle.write('Error Type\tCount\tDescription\n')
            for tpe, count in sorted(types.items(), key=lambda x: x[0].value):
                handle.write("%s\t%d\t%s\n" % (tpe.name, count, tpe.value))

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
            scheme=None

        cls.__validate_options(options, scheme, logger)

        if options.output is None:
            handle = sys.stdout
        else:
            handle = open(options.output, "w")

        errors = ValidationErrors(options.max_errors \
                                      if options.max_errors else sys.maxsize)

        for path in options.input:
            logger.info("Examining %s", path)

            # Gather as many errors as possible
            silent = ValidationStringency.Silent
            reader = MafReader.reader_from(path=path,
                                           validation_stringency=silent,
                                           scheme=scheme)

            if not cls.__process_errors(options, reader, logger,
                                        handle, errors):
                n = 0
                for _ in reader:
                    if cls.__process_errors(options, reader, logger,
                                            handle, errors):
                        break
                    n = n + 1
                    if n % Validate.print_every_n_records == 0:
                        logger.info("Processed %d records" % n)
                if n == 0 or n % Validate.print_every_n_records != 0:
                    logger.info("Processed %d records" % n)

            reader.close()

            cls.__print_report(options, errors, handle)

        if options.output:
            handle.close()

@unique
class Mode(Enum):
    """A simple enumeration for the validation report mode"""
    Summary = 1
    Verbose = 2
