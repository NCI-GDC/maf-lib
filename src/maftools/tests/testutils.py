import os
import tempfile

from maflib.tests.testutils import tmp_file
from maflib.util import captured_output
from maftools.__main__ import main


def test_main(subcommand, lines,
              main_args = None,
              subcommand_args = None,
              to_stdout=False):
    in_fh, in_fn = tmp_file(lines=lines)
    in_fh.close()

    out_fh, out_fn = tempfile.mkstemp()

    if not main_args:
        main_args = []
    main_args.extend([subcommand, "--input", str(in_fn)])
    if not to_stdout:
        main_args.extend(["--output", str(out_fn)])
    if subcommand_args:
        main_args.extend(subcommand_args)

    with captured_output() as (stdout, stderr):
        main(args=main_args)

    fh = open(out_fn, "r")
    out_lines = [line.rstrip("\r\n") for line in fh]
    fh.close()

    stdout = stdout.getvalue().rstrip('\r\n').split("\n")
    stderr = stderr.getvalue().rstrip('\r\n').split("\n")

    os.remove(in_fn)
    os.remove(out_fn)

    return (out_lines, stdout, stderr)