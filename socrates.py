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

    # add the current directory to Python's path; this will allow us to
    # do imports of modules from where socrates is invoked
    sys.path.append(os.getcwd())

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

    if args.mode == 'grade':
        import grader

        try:
            c = criteria.Criteria.from_json(args.criteria_file)
        except FileNotFoundError:
            util.sprint("criteria file does not exist", error=True)
            sys.exit(8)
        except ValueError as err:
            util.sprint("error importing criteria: {}".format(err), error=True)
            sys.exit(5)

        grader.grade(c, args.submission_file, c.short_name + "-grade.txt")
