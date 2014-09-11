#!/usr/local/bin/python3.3

import os
import sys

import cmdline
import util
import criteria

# triggers discovery of file and test types (see filetypes/__init__.py)
import filetypes


if __name__ == '__main__':
    args = cmdline.get_args()

    if args.quiet:
        util.quiet_mode = True

    if args.mode in ['generate', 'gen']:
        plain_files = []
        for file_path in args.solution_file:
            plain_file = filetypes.plainfile.PlainFile(path=file_path,
                                                       point_value=0,
                                                       tests=None)
            plain_files.append(plain_file)

        crit = criteria.Criteria(assignment_name="generated assignment",
                                 short_name="replaceme",
                                 course_name="CS 101 at Acme College",
                                 files=plain_files)
        crit.to_json()
        sys.exit(0)

    if args.mode == 'grade':
        import grader
        try:
            c = criteria.Criteria.from_json(args.criteria_file)
        except FileNotFoundError:
            util.sprint("criteria file does not exist", error=True)
            sys.exit(8)
        except ValueError as err:
            util.sprint("error importing criteria: {}".format(err),
                        error=True)
            sys.exit(5)

        grade_filename = c.short_name + "-grade.txt"

        if os.path.isfile(grade_filename):
            util.sprint("refusing to overwrite existing grade file")
            sys.exit(6)

        grader.grade(c, args.submission_files, grade_filename)
        sys.exit(0)

    elif args.mode == 'batch':
        import os
        import inspect
        import subprocess

        proc = os.path.abspath(inspect.getfile(inspect.currentframe()))
        crit_path = os.path.abspath(args.criteria_file)

        for subdir in args.submission_dirs:
            if not os.path.isdir(subdir):
                util.sprint("invalid submission directory "
                            "'{}'".format(subdir), error=True)

            util.sprint("changing into '{}'".format(subdir))
            os.chdir(subdir)

            files_here = os.listdir(os.curdir)
            subprocess.call([proc, "grade", crit_path] + files_here)

            os.chdir(os.pardir)

        sys.exit(0)
