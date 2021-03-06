"""Various utility functions and variables."""

import sys
import os
import builtins
import signal

import blessed

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
ERR_NO_EDITOR = 12
ERR_ABNORMAL_HOOK_EXIT = 14
ERR_SCRIPT_RUNTIME_ERROR = 15

EXIT_WITH_MISSING = 100
EXIT_WITH_DEFER = 101

ALPHABET = [chr(ord('a') + i) for i in range(26)] + \
           [chr(ord('A') + i) for i in range(26)]

ALPHANUMERICS = ALPHABET + [str(i) for i in range(10)]

terminal = blessed.Terminal()
_ui = False

_prog_name = os.path.basename(sys.argv[0])


def green(string):
    return terminal.green(string)


def yellow(string):
    return terminal.yellow(string)


def print(string, end='\n'):
    builtins.print(string)


def info(string):
    print(_prog_name + ': ' + terminal.blue(string))


def warning(string):
    print(_prog_name + ': ' + terminal.yellow(string))


def error(string):
    print(_prog_name + ': ' + terminal.red(string))


def print_traceback():
    from traceback import print_exc
    print_exc()


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


def exit(exit_code, hooks=True, traceback=True):
    """The safe way to cause socrates to exit immediately.
    If the 'hooks' argument is True, this function will try to
    run hooks attached to 'before_exit' before actually exiting.
    """
    from hooks import run_hooks_for

    if hooks:
        run_hooks_for('before_exit')

    if _ui:
        ui_stop()

    if traceback:
        type, value, tb = sys.exc_info()
        if tb is not None:
            print_traceback()

    sys.exit(exit_code)


def ui_start():
    global _ui
    _ui = True


def ui_stop():
    global _ui
    _ui = False
