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

    # parser for grade mode
    norm_mode_opts = {'description': "Start an interactive grading session"}
    norm_mode_parser = subparsers.add_parser('grade', **norm_mode_opts)

    assignment_opts = {'help': 'assignment name, with group (e.g., "ps2a")'}
    norm_mode_parser.add_argument('assignment_with_group', **assignment_opts)

    input_opts = {'help': "submission file(s) to grade",
                  'nargs': '*'}
    norm_mode_parser.add_argument('submission_files', **input_opts)


    # parser for batch mode
    batch_mode_opts = {'description': "Start grading in batch mode"}
    batch_mode_parser = subparsers.add_parser('batch', **batch_mode_opts)

    assignment_opts = {'help': 'assignment name, with group (e.g., "ps2a")'}
    batch_mode_parser.add_argument('assignment_with_group', **assignment_opts)

    input_opts = {'help': "submission directories, one per student",
                  'nargs': '*'}
    batch_mode_parser.add_argument('submission_dirs', **input_opts)


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
    config_mode_parser = subparsers.add_parser('config', **config_mode_opts)


    # parser for activity mode
    act_mode_opts = {'description': "See what grades graders have submitted "
                                    "for a given assignment"}
    act_mode_parser = subparsers.add_parser('activity', **act_mode_opts)

    assignment_opts = {'help': "the short name of the assignment, "
                               "with no group",
                       'nargs': 1}
    act_mode_parser.add_argument('assignment', **assignment_opts)

    args = top_parser.parse_args()

    if not args.mode:
        top_parser.parse_args(['-h'])
        sys.exit(util.ERR_ARGS)

    return args


if __name__ == '__main__':
    print("To use socrates, run the 'socrates' module.")
