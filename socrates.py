"""A grading toolkit for programming assignments in Python."""


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
        return False

    return args


if __name__ == '__main__':
    import sys

    args = _handle_args()

    if not args:
        sys.exit(1)

    if args.mode in ['generate', 'gen']:
        import files

        crit = files.generate(args.solution_file)
        out_filename = files.to_json(crit)

        print("Wrote criteria to {}.".format(out_filename))

    if args.mode == 'grade':
        import grader

        session = grader.GradingSession(criteria_file=args.criteria_file,
                                        submissions=args.submission_file)

        session.start()

