"""Various utility functions and variables."""

import sys


COLOR_RED='\033[91m'
COLOR_GREEN='\033[92m'
COLOR_YELLOW='\033[93m'
COLOR_BLUE='\033[94m'
COLOR_CYAN='\033[96m'
COLOR_INVERTED='\033[7m'
COLOR_RESET='\033[0m'

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
