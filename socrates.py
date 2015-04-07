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
import hooks

# conditions that are deemed "okay" to be returned by a subprocess when
# socrates is run in batch mode
OKAY_CONDITIONS = [util.EXIT_WITH_MISSING, util.ERR_GRADE_FILE_EXISTS,
                   util.EXIT_WITH_DEFER]

CRITERIA_FILE_PATTERN = r'^[a-z]+\d+[a-z]$'


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

    if args.mode == 'edit':
        _edit(args)

    if args.mode in ['grade', 'submit']:
        try:
            sname, group = _parse_assignment_name(args.assignment_with_group)
        except ValueError as err:
            util.sprint(str(err) + ': ' + args.assignment_with_group,
                        error=True)
            sys.exit(util.ERR_BAD_ASSIGNMENT)

        criteria_path = _form_criteria_path(sname, group)

        if not os.path.isfile(criteria_path):
            message = "could not find criteria file for {}"
            message = message.format(sname)

            if group:
                message += ", group " + group

            util.sprint(message, error=True)
            sys.exit(util.ERR_CRITERIA_MISSING)

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


def _config():
    """Handles 'config' mode."""
    from inspect import getmembers, ismodule

    for member_name, member_val in getmembers(config):
        if member_name[0] != '_' and not ismodule(member_val):
            print("{}: {}".format(member_name, member_val))


def _edit(args):
    """Handles 'edit' mode. This function creates a temporary file and
    tries to use the user's default editor to edit the specified criteria
    file. If the new file has a syntax error or is missing essential
    components, the user is prompted to edit again or stop.
    """
    import tempfile
    import shutil
    import filecmp
    import subprocess

    import criteria
    from prompt import prompt

    isfile = os.path.isfile

    try:
        short_name, group = _parse_assignment_name(args.assignment_with_group)
    except ValueError as err:
        util.sprint(str(err) + ': ' + args.assignment_with_group, error=True)
        sys.exit(util.ERR_BAD_ASSIGNMENT)

    existing_path = _form_criteria_path(short_name, group)

    if not isfile(existing_path):
        util.warn("the file '{}' does not exist".format(existing_path))

        choices = ["create and edit this criteria file now",
                   "exit without creating anything"]

        selections = prompt(choices, mode='1')
        if 1 in selections:
            util.sprint("exiting without changing anything")
            return

    temp_file, temp_path = tempfile.mkstemp(suffix='.yml')

    # copy contents of existing file into temp file
    if isfile(existing_path):
        shutil.copyfile(existing_path, temp_path)

    while True:
        # try to open editor with file
        _edit_file(temp_path)

        try:
            _ = criteria.Criteria.from_yaml(temp_path)

        except Exception as e:
            import traceback

            util.sprint("proposed criteria file produced an error",
                        color=util.COLOR_RED)

            traceback.print_exc()

            choices = ["return to the editor to fix the problem",
                       "abort the change (existing file will not change)"]

            selections = prompt(choices, mode='1')

            if 0 in selections:
                continue
            else:
                util.sprint("exiting without changing anything")
                break

        else:
            # temporary file contains valid, new version of the criteria file;
            # if the temporary file is any different, we will copy it over
            # the old file

            if isfile(existing_path) and \
               filecmp.cmp(temp_path, existing_path, shallow=False):
                # files seem to be the same
                util.sprint("no changes made; exiting without " +
                            "changing original", color=util.COLOR_YELLOW)
                os.remove(temp_path)

            else:
                # files are different; copy over the old file
                shutil.copyfile(temp_path, existing_path)

                # remove temporary file
                os.remove(temp_path)

                util.sprint("{} updated".format(existing_path),
                            color=util.COLOR_YELLOW)

            break


def _grade(args, criteria_object, grade_filename):
    """Handles 'grade' mode. Most of the work is handed off
    to the 'grader' module, which runs interactively.
    """
    import grader
    from prompt import prompt

    if os.path.isfile(grade_filename):
        util.sprint("refusing to overwrite existing grade file",
                    color=util.COLOR_RED)
        sys.exit(util.ERR_GRADE_FILE_EXISTS)

    if not args.submission_files:
        util.sprint("warning: no submission files specified",
                    color=util.COLOR_RED)

    hooks.run_hooks_for('before_file_search')

    any_missing = grader.grade(criteria_object, args.submission_files,
                               grade_filename,
                               assume_missing=args.assume_missing)

    if not args.no_edit:
        util.sprint("please review the following grade file ({}) "
                    "for issues:".format(grade_filename),
                    color=util.COLOR_GREEN)

        with open(grade_filename) as f:
            print(f.read())

        choices = ["edit the grade file now", "do not edit the grade file"]
        selections = prompt(choices, mode='1')

        if 0 in selections:
            _edit_file(grade_filename)

    # TODO this may not actually run if the functions above exit themselves
    hooks.run_hooks_for('before_exit')

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
            os.umask(0o000)
            util.makedirs(dest_path)
        except OSError:
            util.sprint("error making user directory in dropbox", error=True)
            sys.exit(util.ERR_DROPBOX_MAKEDIRS)

        dest_path += os.sep + grade_filename
        shutil.copyfile(grade_file_path, dest_path)
        os.chmod(dest_path, 0o666)

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

        sub_args = [proc, '--log', 'grade']

        if args.no_edit:
            sub_args.append("--no-edit")

        if args.assume_missing:
            sub_args.append("--assume-missing")

        sub_args.append(args.assignment_with_group)

        try:
            return_val = subprocess.call(sub_args + files_here)

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


def _parse_assignment_name(short_name_with_group):
    """Given a short assignment name with a group (e.g., "ps4a"),
    return the assignment's short name ("ps4") and the group
    ("a") in a tuple.
    """
    from re import match

    m = match(CRITERIA_FILE_PATTERN, short_name_with_group)
    if not m:
        raise ValueError("invalid assignment name")

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


def _edit_file(path):
    """Attempts to consult the $EDITOR environment variable for the user's
    favorite text editor (otherwise trying to use vi) to edit the file
    specfied by the given path. socrates will wait for the editor to exit
    before continuing.
    """
    import os
    import subprocess
    import shutil

    if 'EDITOR' in os.environ:
        # run $EDITOR with the grade file
        subprocess.call([os.environ['EDITOR'], path])

    elif shutil.which('nano') is not None:
        # try to run nano
        subprocess.call(['nano', path])
        util.sprint("your $EDITOR environment variable is not set")
        util.sprint("if you set $EDITOR, socrates will use that editor")

    else:
        util.sprint("could not open your favorite text editor or nano",
                    color=util.COLOR_RED)
        sys.exit(util.ERR_NO_EDITOR)


if __name__ == '__main__':
    main(cmdline.get_args())
