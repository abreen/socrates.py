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


def _print_grader_activity(short_name, dropbox):
    import os
    import pwd
    import datetime

    found_grader_subs = []

    for hash_dir in os.listdir(dropbox):
        if hash_dir[0] == '.': continue

        dirpath = dropbox + os.sep + hash_dir

        dir_st = os.stat(dirpath)
        dir_ctime = dir_st.st_mtime

        grader_pw = pwd.getpwuid(dir_st.st_uid)
        grader_name = grader_pw.pw_name
        grader_fullname = grader_pw.pw_gecos

        group = os.listdir(dirpath)[0]

        t = (grader_name, grader_fullname, group, dir_ctime)
        found_grader_subs.append(t)


    util.sprint("grader submission activity:")
    for name, fullname, group, time in found_grader_subs:
        on = datetime.datetime.fromtimestamp(time)
        util.sprint("{} ({}) submitted group {} on {}".format(
                    fullname, name, group, on))


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

    if args.mode in ['grade', 'submit']:
        import grader
        try:
            c = criteria.Criteria.from_yaml(args.criteria_file)
        except FileNotFoundError:
            util.sprint("criteria file does not exist", error=True)
            sys.exit(util.ERR_CRITERIA_MISSING)
        except IsADirectoryError:
            util.sprint("specified criteria is a directory", error=True)
            sys.exit(util.ERR_CRITERIA_IMPORT)
        except:
            import traceback
            err = sys.exc_info()
            util.sprint("error importing criteria: {} ("
                        "{})".format(err[0].__name__, err[1]),
                        error=True)
            traceback.print_exc()
            sys.exit(util.ERR_CRITERIA_IMPORT)

        grade_filename = c.name + (c.group if c.group else "") + "-grade.txt"

    if args.mode == 'grade':
        if os.path.isfile(grade_filename):
            util.sprint("refusing to overwrite existing grade file")
            sys.exit(util.ERR_GRADE_FILE_EXISTS)

        if not args.submission_files:
            util.sprint("warning: no submission files specified")

        any_missing = grader.grade(c, args.submission_files, grade_filename)
        if any_missing:
            sys.exit(util.EXIT_WITH_MISSING)
        else:
            sys.exit()

    elif args.mode == 'submit':
        from functools import reduce
        import tarfile
        import random

        chars = [str(i) for i in range(10)] + \
                [chr(ord('a') + i) for i in range(26)]

        rand = reduce(str.__add__, [random.choice(chars) for _ in range(32)])
        submit_dir = config.dropbox_dir + os.sep + c.name + \
                     os.sep + rand + (os.sep + c.group if c.group else "")

        if not os.path.isdir(config.dropbox_dir + os.sep + c.name):
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

            okay_conditions = [util.EXIT_WITH_MISSING, util.ERR_GRADE_FILE_EXISTS,
                               util.EXIT_WITH_DEFER]

            if rv != 0 and rv not in okay_conditions:
                util.sprint("child process encountered an error", error=True)
                os.chdir(os.pardir)
                sys.exit(rv)

            util.sprint("completed subdirectory '{}'".format(subdir))
            os.chdir(os.pardir)

        sys.exit()

    elif args.mode in ['websubmit', 'ws']:
        short_name = args.assignment_name[0]
        dropbox = config.dropbox_dir + os.sep + short_name

        if not os.path.isdir(dropbox):
            util.sprint("no dropbox for assignment '{}'".format(short_name),
                        error=True)
            sys.exit(util.ERR_BAD_DROPBOX)

        if args.activity:
            _print_grader_activity(short_name, dropbox)
            sys.exit()

        import tarfile
        import re

        found_groups = []
        found_students = dict()

        for hash_dir in os.listdir(dropbox):
            if hash_dir[0] == '.': continue

            dirpath = dropbox + os.sep + hash_dir
            group = os.listdir(dirpath)[0]

            if group not in found_groups:
                found_groups.append(group)

            for student_tar in os.listdir(dirpath + os.sep + group):
                if student_tar[0] == '.': continue

                path = dirpath + os.sep + group + os.sep + student_tar
                mtime = os.stat(path).st_mtime

                username = student_tar[:student_tar.index('.')]
                if username in found_students:
                    if group in found_students[username]:
                        if mtime > found_students[username][group][0]:
                            found_students[username][group] = (mtime, path)
                    else:
                        found_students[username][group] = (mtime, path)
                else:
                    found_students[username] = dict()
                    found_students[username][group] = (mtime, path)


        ws_name = input(util.COLOR_BLUE + "enter WebSubmit's name for this "
                        "assignment (e.g., hw00): " + util.COLOR_RESET)

        ws_course = input(util.COLOR_BLUE + "enter WebSubmit's name for this "
                          "course (e.g., cs111): " + util.COLOR_RESET)

        target_dir = ws_course + '-' + ws_name
        os.mkdir(target_dir)

        total_pat = re.compile("[tT]otal:\s*(\d+(?:\.\d+)?)")

        for username, groups in found_students.items():
            compiled = []
            points = 0

            # we want the earlier parts to come first in the compiled
            # grade file, so we sort the group keys
            sgroups = sorted(groups)
            for g in sgroups:
                tar_path = groups[g][1]

                with tarfile.open(tar_path) as tar:
                    grd_file_path = username + os.sep + short_name + g + \
                                    '-grade.txt'
                    grade_file = tar.extractfile(grd_file_path)

                    for line in grade_file:
                        line = line.decode('utf-8')
                        m = total_pat.match(line)
                        if m:
                            points += float(m.group(1))
                        else:
                            compiled.append(line)

            os.mkdir(target_dir + os.sep + username)
            path = target_dir + os.sep + username + os.sep
            grade_file_path = path + ws_name + '-' + username + '.txt'

            with open(grade_file_path, 'w') as f:
                f.write(''.join(compiled))
                f.write('\n')
                f.write("Total: {}\n".format(points))

            util.sprint("wrote '{}'".format(grade_file_path))

        util.sprint("collected grade files into '{}'".format(target_dir))
        util.sprint("(\"zip\" this file and upload to WebSubmit!)")


