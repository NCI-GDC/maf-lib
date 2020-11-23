#!/usr/bin/env python3

import tempfile
import unittest

from maflib.logger import Logger
from maflib.validation import (
    MafFormatException,
    MafValidationError,
    MafValidationErrorType,
    ValidationStringency,
)


class TestMafValidationError(unittest.TestCase):

    __errors = (
        MafValidationError(
            tpe=MafValidationErrorType.HEADER_LINE_EMPTY_KEY,
            message="Error with line number",
        ),
        MafValidationError(
            tpe=MafValidationErrorType.HEADER_LINE_MISSING_START_SYMBOL,
            message="Error without line number",
            line_number=42,
        ),
    )

    def test_str(self):
        actual_strings = [str(error) for error in TestMafValidationError.__errors]
        expected_strings = [
            "Error with line number",
            "On line number 42: Error without line number",
        ]
        self.assertTrue(len(actual_strings) == len(expected_strings))
        for actual, expect in zip(actual_strings, expected_strings):
            self.assertIn(expect, actual)

    def test_process_validation_errors_strict(self):
        logger = Logger.get_logger("test_process_validation_errors_strict")
        with self.assertRaises(MafFormatException) as context:
            MafValidationError.process_validation_errors(
                validation_errors=TestMafValidationError.__errors,
                validation_stringency=ValidationStringency.Strict,
                logger=logger,
            )
        self.assertIn("Error with line number", str(context.exception))
        self.assertTrue(
            context.exception.tpe, MafValidationErrorType.HEADER_LINE_EMPTY_KEY
        )

    def test_process_validation_errors_lenient(self):
        err_stream = tempfile.NamedTemporaryFile(delete=False, mode="w")
        err_file_name = err_stream.name
        logger = Logger.get_logger(err_file_name, stream=err_stream)

        MafValidationError.process_validation_errors(
            validation_errors=TestMafValidationError.__errors,
            validation_stringency=ValidationStringency.Lenient,
            logger=logger,
        )
        err_stream.close()

        reader = open(err_file_name, "r")
        actual_lines = reader.readlines()
        expected_lines = [
            MafValidationError.ignore_message(error)
            for error in TestMafValidationError.__errors
        ]
        reader.close()

        self.assertTrue(len(actual_lines) == len(expected_lines))
        for actual_line, expected_line in zip(actual_lines, expected_lines):
            self.assertIn(expected_line, actual_line)


# __END__
