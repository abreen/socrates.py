"""Command line argument handling for socrates."""

import sys
import argparse

import util


def get_args():
    top_opts = {'description': "Grade student work from the command line",
                'epilog': "(try socrates generate -h, "
                          "socrates grade -h, or "
                          "socrates submit -h)"}

    top_parser = argparse.ArgumentParser(**top_opts)
    top_parser.add_argument('-q', '--quiet', action='store_true')
    top_parser.add_argument('-l', '--log', action='store_true')

    subparsers = top_parser.add_subparsers(dest='mode')

    # parser for generate mode
    gen_mode_opts = {'description': "Generate a JSON criteria file from an "
                                    "existing solution",
                     'aliases': ['gen']}
    gen_mode_parser = subparsers.add_parser('generate', **gen_mode_opts)

    sol_opts = {'help': "file(s) for which to generate criteria",
                'nargs': '*'}
    gen_mode_parser.add_argument('solution_file', **sol_opts)


    # parser for grading mode
    norm_mode_opts = {'description': "Start an interactive grading session"}
    norm_mode_parser = subparsers.add_parser('grade', **norm_mode_opts)

    criteria_opts = {'help': "criteria file in JSON or YAML format"}
    norm_mode_parser.add_argument('criteria_file', **criteria_opts)

    input_opts = {'help': "submission file(s) to grade",
                  'nargs': '*'}
    norm_mode_parser.add_argument('submission_files', **input_opts)


    # parser for batch mode
    batch_mode_opts = {'description': "Start grading in batch mode"}
    batch_mode_parser = subparsers.add_parser('batch', **batch_mode_opts)

    criteria_opts = {'help': "criteria file in JSON or YAML format"}
    batch_mode_parser.add_argument('criteria_file', **criteria_opts)

    input_opts = {'help': "submission directories, one per student",
                  'nargs': '*'}
    batch_mode_parser.add_argument('submission_dirs', **input_opts)


    # parser for submit mode
    submit_mode_opts = {'description': "Submit graded files"}
    submit_mode_parser = subparsers.add_parser('submit', **submit_mode_opts)

    criteria_opts = {'help': "criteria file in JSON or YAML format"}
    submit_mode_parser.add_argument('criteria_file', **criteria_opts)

    input_opts = {'help': "submission directories, one per student",
                  'nargs': '*'}
    submit_mode_parser.add_argument('submission_dirs', **input_opts)


    # parser for config mode
    config_mode_opts = {'description': "Print current configuration"}
    config_mode_parser = subparsers.add_parser('config', **config_mode_opts)


    # parser for WebSubmit mode
    ws_mode_opts = {'description': "Collect individual grades into one "
                                   "directory for upload to WebSubmit",
                    'aliases': ['ws']}
    ws_mode_parser = subparsers.add_parser('websubmit', **ws_mode_opts)

    assignment_opts = {'help': "the short name for the assignment",
                       'nargs': 1}
    ws_mode_parser.add_argument('assignment_name', **assignment_opts)

    activity_opts = {'help': "see log of grader submission activity",
                     'action': 'store_true'}
    ws_mode_parser.add_argument('--activity', **activity_opts)

    args = top_parser.parse_args()

    if not args.mode:
        top_parser.parse_args(['-h'])
        sys.exit(util.ERR_ARGS)

    return args


if __name__ == '__main__':
    print("To use socrates, run the 'socrates' module.")
