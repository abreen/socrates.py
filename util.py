"""Various utility functions and variables."""

import sys


COLOR_RED = '\033[91m'
COLOR_GREEN = '\033[92m'
COLOR_YELLOW = '\033[93m'
COLOR_BLUE = '\033[94m'
COLOR_CYAN = '\033[96m'
COLOR_INVERTED = '\033[7m'
COLOR_RESET = '\033[0m'

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

# TODO these should go to config?
quiet_mode = False
log_file = None
sprint_prefix = ""


def sprint(string, error=False, color=COLOR_BLUE):
    """A utility function for printing messages to the standard out
    or standard error. Implementation note: always use this function
    for printing, unless "raw" output from a file is being displayed.
    """
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


def escape(str_):
    """Given a string, return a string where any newlines or tab characters
    have been replaced with their backslashed strings (e.g., "\\t").
    """
    return str_.replace('\n', '\\n').replace('\t', '\\t')


def prepend_lines(lines, pre):
    """Given a list of strings, each a "line" of some block of text,
    return a new list of strings, where each string in the list is
    prepended with the specified string.
    """
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


def add_to(item, list_):
    """Add an item to a list. If the item is a list itself, the list is
    extended. Otherwise, the item is appended to the list.
    """
    if type(item) is list:
        list_.extend(item)
    else:
        list_.append(item)


def plural(str_, num):
    """Return the pluralized version of the specified string, given the
    specified quantity. If the quantity is not 1, the returned string is
    pluralized.
    """
    return str_ + ("s" if num != 1 else "")
