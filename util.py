"""Various utility functions and variables."""

import sys


COLOR_RED='\033[91m'
COLOR_GREEN='\033[92m'
COLOR_YELLOW='\033[93m'
COLOR_BLUE='\033[94m'
COLOR_CYAN='\033[96m'
COLOR_RESET='\033[0m'

quiet_mode = False
sprint_prefix = ""


def sprint(string, error=False, color=COLOR_BLUE):
    if quiet_mode: return

    first = sprint_prefix

    if error:
        color=COLOR_RED
        first += "{}error:{} ".format(COLOR_RED, COLOR_RESET)

    msg = color + string + COLOR_RESET

    print(first + msg, file=sys.stderr if error else sys.stdout)


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

