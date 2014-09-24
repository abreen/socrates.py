#!/usr/bin/env python3.3

import os
import sys
import datetime

import cmdline
import util
import criteria

# triggers discovery of file and test types (see filetypes/__init__.py)
import filetypes

# loads configuration file
import config


if __name__ == '__main__':
    args = cmdline.get_args()

    if args.quiet:
        util.quiet_mode = True

    if args.log:
        util.log_file = open("socrates-log.txt", 'a')
        now = datetime.datetime.today()
        util.log_file.write(str(now) + '\n')

    if args.mode == 'config':
        import inspect
        for m in inspect.getmembers(config):
            if m[0][0] != '_' and not inspect.ismodule(m[1]):
                print("{}: {}".format(m[0], m[1]))

        sys.exit()

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
        sys.exit()

    if args.mode in ['grade', 'submit']:
        import grader
        try:
            c = criteria.Criteria.from_json(args.criteria_file)
        except FileNotFoundError:
            util.sprint("criteria file does not exist", error=True)
            sys.exit(util.ERR_CRITERIA_MISSING)
        except:
            import traceback
            err = sys.exc_info()
            util.sprint("error importing criteria: {} ("
                        "{})".format(err[0].__name__, err[1]),
                        error=True)
            traceback.print_exc()
            sys.exit(util.ERR_CRITERIA_IMPORT)

        grade_filename = c.short_name + "-grade.txt"

    if args.mode == 'grade':
        if os.path.isfile(grade_filename):
            util.sprint("refusing to overwrite existing grade file")
            sys.exit(util.ERR_GRADE_FILE_EXISTS)

        if not args.submission_files:
            util.sprint("warning: no submission files specified")

        grader.grade(c, args.submission_files, grade_filename)
        sys.exit()

    elif args.mode == 'submit':
        from functools import reduce
        import tarfile
        import random

        chars = [str(i) for i in range(10)] + \
                [chr(ord('a') + i) for i in range(26)]

        rand = reduce(str.__add__, [random.choice(chars) for c in range(32)])
        submit_dir = config.dropbox_dir + os.sep + c.short_name + \
                     os.sep + rand + (os.sep + c.group if c.group else '')

        if not os.path.isdir(config.dropbox_dir + os.sep + c.short_name):
            util.sprint("cannot submit: dropbox directory has not been "
                        "set up for this assignment", error=True)
            sys.exit(util.ERR_NO_DROPBOX)

        os.umask(0o022)
        try:
            util.makedirs(submit_dir)
        except:
            util.sprint("error making directories in dropbox", error=True)
            sys.exit(util.ERR_DROPBOX_MAKEDIRS)

        num_submitted = 0
        for subdir in args.submission_dirs:
            if subdir[-1] == os.sep:
                subdir = subdir[:-1]

            if not os.path.isdir(subdir):
                util.sprint("'{}' is not a directory".format(subdir),
                            error=True)
                continue
            elif not os.path.isfile(subdir + os.sep + grade_filename):
                util.sprint("not submitting '{}': directory has no "
                            "grade file".format(subdir))
                continue

            tar_path = submit_dir + os.sep + subdir + '.tgz'
            with tarfile.open(tar_path, 'w:gz') as tar:
                tar.add(subdir)

            num_submitted += 1

            util.sprint("wrote '{}' to dropbox".format(tar_path))

        util.sprint("submitted {} graded directories".format(num_submitted))
        sys.exit()

    elif args.mode == 'batch':
        import inspect
        import subprocess

        proc = os.path.abspath(inspect.getfile(inspect.currentframe()))
        crit_path = os.path.abspath(args.criteria_file)

        for subdir in args.submission_dirs:
            if not os.path.isdir(subdir):
                util.sprint("invalid submission directory "
                            "'{}'".format(subdir), error=True)
                continue

            os.chdir(subdir)
            files_here = os.listdir(os.curdir)
            util.sprint("running socrates in '{}'".format(subdir))

            try:
                rv = subprocess.call([proc, "--log", "grade", crit_path] +
                                     files_here)
            except KeyboardInterrupt:
                util.sprint("\nparent stopping (received interrupt)")
                util.sprint("stopped while grading '{}'".format(subdir))
                os.chdir(os.pardir)
                sys.exit(util.ERR_INTERRUPTED)

            if rv != 0 and rv != util.ERR_GRADE_FILE_EXISTS:
                util.sprint("child process encountered an error",
                            error=True)
                os.chdir(os.pardir)
                sys.exit(rv)

            util.sprint("completed subdirectory '{}'".format(subdir))
            os.chdir(os.pardir)

        sys.exit()

