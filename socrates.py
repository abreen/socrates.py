#!/usr/bin/env python3.3

"""The main socrates script (i.e., the one users should invoke from
the command line).
"""

import os
import sys
import datetime

import cmdline
import util
import criteria

import config


# conditions that are deemed "okay" to be returned by a subprocess when
# socrates is run in batch mode
OKAY_CONDITIONS = [util.EXIT_WITH_MISSING, util.ERR_GRADE_FILE_EXISTS,
                   util.EXIT_WITH_DEFER]

def main(args):
    """The function invoked when socrates starts from the command line."""
    if args.quiet:
        util.quiet_mode = True

    if args.log:
        util.log_file = open("socrates-log.txt", 'a')
        now = datetime.datetime.today()
        util.log_file.write(str(now) + '\n')

    if args.mode == 'config':
        _config()

    if args.mode in ['grade', 'submit']:
        try:
            sname, group = _parse_assignment_name(args.assignment_with_group)
        except ValueError as err:
            util.sprint("invalid assignment: " + str(err), error=True)
            sys.exit(util.ERR_BAD_ASSIGNMENT)

        criteria_path = _form_criteria_path(sname, group)
        criteria_object = _create_criteria_object(criteria_path)

        assignment_name, group = criteria_object.name, criteria_object.group
        grade_filename = assignment_name
        if group:
            grade_filename += group
        grade_filename += '-grade.txt'

        if args.mode == 'grade':
            _grade(args, criteria_object, grade_filename)

        elif args.mode == 'submit':
            _submit(args, criteria_object, grade_filename)

    elif args.mode == 'batch':
        _batch(args)

    elif args.mode == 'activity':
        _activity(args)


def _config():
    """Handles 'config' mode."""
    from inspect import getmembers, ismodule

    for member_name, member_val in getmembers(config):
        if member_name[0] != '_' and not ismodule(member_val):
            print("{}: {}".format(member_name, member_val))


def _grade(args, criteria_object, grade_filename):
    """Handles 'grade' mode. Most of the work is handed off
    to the 'grader' module, which runs interactively.
    """
    import subprocess
    import shutil

    import grader
    from prompt import prompt

    if os.path.isfile(grade_filename):
        util.sprint("refusing to overwrite existing grade file",
                    color=util.COLOR_RED)
        sys.exit(util.ERR_GRADE_FILE_EXISTS)

    if not args.submission_files:
        util.sprint("warning: no submission files specified",
                    color=util.COLOR_RED)

    any_missing = grader.grade(criteria_object, args.submission_files,
                               grade_filename)

    util.sprint("please review the following grade file ({}) "
                "for issues:".format(grade_filename),
                color=util.COLOR_GREEN)

    with open(grade_filename) as f:
        print(f.read())

    choices = ["edit the grade file now", "do not edit the grade file"]
    selections = prompt(choices, mode='1')

    if 0 in selections:
        if 'EDITOR' in os.environ:
            # run $EDITOR with the grade file
            subprocess.call([os.environ['EDITOR'], grade_filename])

        elif shutil.which('vi') is not None:
            # try to run vi
            subprocess.call(['vi', grade_filename])

        else:
            util.sprint("could not open your favorite text editor or vi",
                        color=util.COLOR_RED)

            sys.exit(util.ERR_NO_EDITOR)

    if any_missing:
        sys.exit(util.EXIT_WITH_MISSING)


def _submit(args, criteria_object, grade_filename, umask=0o002):
    """Handles 'submit' mode. Allows a grader to send completed grade files
    to the "dropbox" directory.
    """
    import shutil

    os.umask(umask)

    num_submitted = 0

    # args.submission_dirs should contain a list of directories whose names
    # are student user names
    for username in args.submission_dirs:
        if username[-1] == os.sep:
            username = username[:-1]            # removes ending '/'

        # check if specified file is a directory
        if not os.path.isdir(username):
            util.sprint("'{}' is not a directory".format(username),
                        error=True)
            continue

        grade_file_path = username + os.sep + grade_filename
        if not os.path.isfile(grade_file_path):
            util.sprint("not submitting '{}': directory has no "
                        "grade file".format(username))
            continue

        # TODO check if directory name is a valid student name

        dest_path = config.dropbox_dir + os.sep + username

        # if this is the first time this user's grades are being submitted,
        # we may need to create the directory in the dropbox
        try:
            util.makedirs(dest_path)
        except OSError:
            util.sprint("error making user directory in dropbox", error=True)
            sys.exit(util.ERR_DROPBOX_MAKEDIRS)

        dest_path += os.sep + grade_filename
        shutil.copyfile(grade_file_path, dest_path)

        num_submitted += 1

        util.sprint("wrote '{}' to dropbox".format(dest_path))

    util.sprint("submitted {} {}".format(num_submitted,
                                         util.plural('grade', num_submitted)))


def _batch(args):
    """Handles 'batch' mode."""
    import inspect
    import subprocess

    # absolute path of the current running Python script
    proc = os.path.abspath(inspect.getfile(inspect.currentframe()))

    for subdir in args.submission_dirs:
        if not os.path.isdir(subdir):
            util.sprint("invalid submission directory "
                        "'{}'".format(subdir), error=True)
            continue

        os.chdir(subdir)

        # this will simulate a user executing socrates grade * at a shell
        files_here = os.listdir(os.curdir)

        util.sprint("running socrates in '{}'".format(subdir))

        try:
            return_val = subprocess.call([proc, "--log", "grade",
                                          args.assignment_with_group] + \
                                          files_here)
        except KeyboardInterrupt:
            util.sprint("\nparent stopping (received interrupt)")
            util.sprint("stopped while grading '{}'".format(subdir))
            os.chdir(os.pardir)
            sys.exit(util.ERR_INTERRUPTED)

        if return_val != 0 and return_val not in OKAY_CONDITIONS:
            util.sprint("child process encountered an error", error=True)
            os.chdir(os.pardir)
            sys.exit(return_val)

        util.sprint("completed subdirectory '{}'".format(subdir))
        os.chdir(os.pardir)


def _activity(args):
    """Handles 'activity' mode."""
    import pwd

    dropbox_path = _get_dropbox_path(args)

    found_grader_subs = []
    for hash_dir in os.listdir(dropbox_path):
        if hash_dir[0] == '.':
            continue

        dirpath = dropbox_path + os.sep + hash_dir

        dir_st = os.stat(dirpath)
        dir_ctime = dir_st.st_mtime

        grader_pw = pwd.getpwuid(dir_st.st_uid)
        grader_name = grader_pw.pw_name
        grader_fullname = grader_pw.pw_gecos

        group = os.listdir(dirpath)[0]

        tup = (grader_name, grader_fullname, group, dir_ctime)
        found_grader_subs.append(tup)

    _print_submission_activity(found_grader_subs)


def _parse_assignment_name(short_name_with_group):
    """Given a short assignment name with a group (e.g., "ps4a"),
    return the assignment's short name ("ps4") and the group
    ("a") in a tuple.
    """
    if short_name_with_group[-1] not in util.ALPHABET:
        raise ValueError("group not specified")

    return short_name_with_group[:-1], short_name_with_group[-1]


def _form_criteria_path(short_name, group):
    """Given an assignment's short name (e.g., "ps4"), and optionally a
    group, use the configuration file data to form a path to the appropriate
    criteria file for the assignment. The path returned by this function
    starts with config.criteria_dir, which is given by the socrates
    configuration file.
    """
    criteria_path = config.criteria_dir + os.sep + short_name
    if group:
        criteria_path += os.sep + short_name + group + '.yml'
    else:
        criteria_path += '.yml'

    if not os.path.isfile(criteria_path):
        message = "could not find criteria file for {}"
        message = message.format(short_name)

        if group:
            message += ", group " + group

        util.sprint(message, error=True)
        sys.exit(util.ERR_CRITERIA_MISSING)

    return criteria_path


def _create_criteria_object(criteria_path):
    """Given a path to a valid criteria file, return a Criteria object
    using that criteria file as a source. This function relies on the
    'criteria' module and its Criteria class. Calling that class'
    constructor is pretty costly.
    """
    try:
        criteria_object = criteria.Criteria.from_yaml(criteria_path)

    except FileNotFoundError:
        util.sprint("criteria file does not exist", error=True)
        sys.exit(util.ERR_CRITERIA_MISSING)

    except IsADirectoryError:
        util.sprint("specified criteria is a directory", error=True)
        sys.exit(util.ERR_CRITERIA_IMPORT)

    return criteria_object


def _get_dropbox_path(args):
    """Given valid arguments from a user, use the configuration file data
    and the assignment specified on the command line to form a path to the
    grading "dropbox", where final grade files should be saved. The path
    returned by this function starts with config.dropbox_dir, which is given
    by the socrates configuration file.
    """
    short_name = args.assignment[0]
    dropbox_path = config.dropbox_dir + os.sep + short_name

    if not os.path.isdir(dropbox_path):
        util.sprint("no dropbox for assignment '{}'".format(short_name),
                    error=True)
        sys.exit(util.ERR_BAD_DROPBOX)

    return dropbox_path


def _print_submission_activity(found_grader_subs):
    """Given a list of tuples containing a grader user name, full name,
    grading group, and submission time, print this information to the
    standard out.
    """
    if len(found_grader_subs) == 0:
        util.sprint("No grader submissions.")
        return

    util.sprint("grader submission activity:")
    for name, fullname, group, time in found_grader_subs:
        submitted_on = datetime.datetime.fromtimestamp(time)
        message = "{} ({}) submitted group {} on {}"
        message = message.format(fullname, name, group, submitted_on)
        util.sprint(message)


if __name__ == '__main__':
    main(cmdline.get_args())
