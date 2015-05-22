"""Command line argument handling for socrates."""

import sys
import argparse

import util


def get_args():
    top_opts = {'description': "Grade student work from the command line",
                'epilog': "(try socrates grade -h, "
                          "socrates batch -h, or "
                          "socrates submit -h)"}

    top_parser = argparse.ArgumentParser(**top_opts)

    subparsers = top_parser.add_subparsers(dest='mode')

    # parser for grade mode
    norm_mode_opts = {'description': "Start an interactive grading session"}
    norm_mode_parser = subparsers.add_parser('grade', **norm_mode_opts)

    assignment_opts = {'help': 'assignment name, with group (e.g., "ps2a")'}
    norm_mode_parser.add_argument('assignment_with_group', **assignment_opts)

    input_opts = {'help': "submission file(s) to grade",
                  'nargs': '*'}
    norm_mode_parser.add_argument('submission_files', **input_opts)

    norm_mode_parser.add_argument('--assume-missing',
                                  help="do not prompt for misnamed files",
                                  action='store_true')
    norm_mode_parser.add_argument('--no-edit',
                                  help="do not ask to edit grade file",
                                  action='store_true')


    # parser for batch mode
    batch_mode_opts = {'description': "Start grading in batch mode"}
    batch_mode_parser = subparsers.add_parser('batch', **batch_mode_opts)

    assignment_opts = {'help': 'assignment name, with group (e.g., "ps2a")'}
    batch_mode_parser.add_argument('assignment_with_group', **assignment_opts)

    input_opts = {'help': "submission directories, one per student",
                  'nargs': '*'}
    batch_mode_parser.add_argument('submission_dirs', **input_opts)

    batch_mode_parser.add_argument('--assume-missing',
                                   help="do not prompt for misnamed files",
                                   action='store_true')
    batch_mode_parser.add_argument('--no-edit',
                                   help="do not ask to edit grade file",
                                   action='store_true')


    # parser for submit mode
    submit_mode_opts = {'description': "Submit graded files"}
    submit_mode_parser = subparsers.add_parser('submit', **submit_mode_opts)

    assignment_opts = {'help': 'assignment name, with group (e.g., "ps2a")'}
    submit_mode_parser.add_argument('assignment_with_group', **assignment_opts)

    input_opts = {'help': "submission directories, one per student",
                  'nargs': '*'}
    submit_mode_parser.add_argument('submission_dirs', **input_opts)


    # parser for config mode
    config_mode_opts = {'description': "Print current configuration"}
    subparsers.add_parser('config', **config_mode_opts)


    # parser for edit mode
    edit_mode_opts = {'description': "Safely edit a criteria file"}
    edit_mode_parser = subparsers.add_parser('edit', **edit_mode_opts)

    assignment_opts = {'help': 'assignment name, with group (e.g., "ps2a")'}
    edit_mode_parser.add_argument('assignment_with_group', **assignment_opts)


    args = top_parser.parse_args()

    if not args.mode:
        top_parser.parse_args(['-h'])
        util.exit(util.ERR_ARGS)

    return args


if __name__ == '__main__':
    print("To use socrates, run the 'socrates' module.")
