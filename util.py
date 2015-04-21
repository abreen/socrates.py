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

_bar_left = ''
_bar_center = 'socrates'
_bar_right = os.path.basename(os.getcwd())

_ui = False


def set_mode(mode):
    global _bar_left
    _bar_left = mode.upper()


def green(string):
    return terminal.green(string)

def yellow(string):
    return terminal.yellow(string)


def print(string, end='\n'):
    builtins.print(string)
    if _ui: ui_redraw()


def info(string):
    print(terminal.blue(string))


def warning(string):
    print(terminal.yellow(string))


def error(string):
    print(terminal.red(string))


def print_traceback():
    from traceback import print_exc
    print_exc()
    if _ui: ui_redraw()


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


def exit(exit_code, hooks=True):
    """The safe way to cause socrates to exit immediately.
    If the 'hooks' argument is True, this function will try to
    run hooks attached to 'before_exit' before actually exiting.
    """
    from hooks import run_hooks_for

    if hooks:
        run_hooks_for('before_exit')

    if _ui:
        ui_stop()

    type, value, traceback = sys.exc_info()
    if traceback is not None:
        print_traceback()

    sys.exit(exit_code)


def ui_start():
    global _ui
    builtins.print(terminal.enter_fullscreen(), end='')
    builtins.print(terminal.clear(), end='\n')
    _ui = True


def ui_stop():
    global _ui
    builtins.print('\n' + terminal.exit_fullscreen(), end='')
    _ui = False


def ui_redraw():
    if not _ui:
        return

    t = terminal

    chars = len(_bar_left) + len(_bar_center) + len(_bar_right)
    spaces = t.width - chars

    bar = t.green_reverse(_bar_left + (' ' * (spaces // 2)))
    bar += t.bold_green_reverse(_bar_center)
    bar += t.green_reverse((' ' * (spaces // 2)) + _bar_right)

    with t.location(y=0):
        builtins.print(bar, end='')
