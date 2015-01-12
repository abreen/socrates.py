"""Various utility functions and variables."""

import sys


COLOR_RED='\033[91m'
COLOR_GREEN='\033[92m'
COLOR_YELLOW='\033[93m'
COLOR_BLUE='\033[94m'
COLOR_CYAN='\033[96m'
COLOR_INVERTED='\033[7m'
COLOR_RESET='\033[0m'

ERR_ARGS = 1
ERR_INTERRUPTED = 2
ERR_CRITERIA_MISSING = 3
ERR_CRITERIA_IMPORT = 4
ERR_GRADE_FILE_EXISTS = 5
ERR_GRADING_MISC = 6
ERR_NO_DROPBOX = 7
ERR_DROPBOX_MAKEDIRS = 8
ERR_BAD_CONFIG = 9
ERR_BAD_DROPBOX = 10
ERR_BAD_ASSIGNMENT = 11

EXIT_WITH_MISSING = 100
EXIT_WITH_DEFER = 101

ALPHABET = [chr(ord('a') + i) for i in range(26)] + \
           [chr(ord('A') + i) for i in range(26)]

ALPHANUMERICS = ALPHABET + [str(i) for i in range(10)]

quiet_mode = False
log_file = None
sprint_prefix = ""


def sprint(string, error=False, color=COLOR_BLUE):
    pre = COLOR_RED if error else color
    post = COLOR_RESET

    err = "error: " if error else ""

    stream = sys.stderr if error else sys.stdout

    if log_file:
        print(err + string, file=log_file)

    if not quiet_mode:
        print(pre + sprint_prefix + err + string + post, file=stream)


def heading(string, level=1):
    """Given a string and an optional heading level, return a string
    in setext/atx style (setext for levels 1 and 2, and atx style for
    levels > 2). Returned header strings have a newline.
    """
    if level == 1:
        return string + '\n' + ('=' * len(string)) + '\n'
    elif level == 2:
        return string + '\n' + ('-' * len(string)) + '\n'
    else:
        return ('#' * level) + ' ' + string + '\n'


def escape(s):
    return s.replace('\n', '\\n').replace('\t', '\\t')


def prepend_lines(lines, pre):
    return '\n'.join(map(lambda x: pre + x, lines.split('\n')))


def makedirs(dirpath):
    """Recursively create directories up to the leaf directory, if they
    do not already exist.
    """
    import os

    head, tail = os.path.split(dirpath)
    if tail == '':
        # root directory or current relative root has been reached
        return
    else:
        # make all parent directories
        makedirs(head)

        # make this directory if it does not exist
        if not os.path.isdir(dirpath):
            os.mkdir(dirpath)


def add_to(a, b):
    """Add the first argument (a) to the second argument (b), where the
    b is a list. If a is not a list, it is appended to b. If a is a
    list, the items of a are appended to b, in order.
    """
    if type(a) is list:
        for i in a:
            b.append(i)
    else:
        b.append(a)


def plural(s, n):
    return s + ("s" if n != 1 else "")
