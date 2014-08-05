"""A grading toolkit for programming assignments in Python."""

import os
import sys

from util import *
import files


def _handle_args():
    import argparse

    top_opts = { 'description': "Grade student work from the command line",
                 'epilog': "(try socrates.py generate -h or "
                           "socrates.py grade -h)" }

    top_parser = argparse.ArgumentParser(**top_opts)
    subparsers = top_parser.add_subparsers(dest='mode')

    # parser for generate mode
    gen_mode_opts = { 'description': "Generate a JSON criteria file from an "
                                     "existing solution",
                      'aliases': ['gen'] }
    gen_mode_parser = subparsers.add_parser('generate', **gen_mode_opts)

    sol_opts = { 'help': "Python file for which to generate criteria" }
    gen_mode_parser.add_argument('solution_file', **sol_opts)

    # parser for grading mode
    norm_mode_opts = { 'description': "Start an interactive grading session" }
    norm_mode_parser = subparsers.add_parser('grade', **norm_mode_opts)

    criteria_opts = { 'help': "criteria file in JSON format" }
    norm_mode_parser.add_argument('criteria_file', **criteria_opts)

    input_opts = { 'help': "Python file(s) to grade",
                   'nargs': '+' }
    norm_mode_parser.add_argument('submission_file', **input_opts)


    args = top_parser.parse_args()

    if not args.mode:
        top_parser.parse_args(['-h'])
        system.exit(1)

    return args



if __name__ == '__main__':
    args = _handle_args()

    # add the current directory to Python's path; this will allow us to
    # do imports of modules from where socrates is invoked
    sys.path.append(os.getcwd())

    if args.mode in ['generate', 'gen']:
        # add path to enclosing directory of solution module
        # (we do this because files.generate() will try to import the module)
        sys.path.append(os.path.split(args.solution_file)[0])

        # generate Criteria object from Python solution
        try:
            crit = files.generate(args.solution_file)
        except ImportError as err:
            sprint("error importing module: {}".format(err), error=True)
            sys.exit(1)
        except Exception as exc:
            sprint("bug in solution: {}".format(exc), error=True)
            sys.exit(1)

        # convert Criteria object to JSON format and write to file
        out_filename = files.to_json(crit)

    if args.mode == 'grade':
        import grader

        # decode JSON criteria file into Criteria object
        criteria = files.from_json(args.criteria_file)

        # interactively grade submissions using criteria and write grade file
        grader.grade(criteria, args.submission_file)

