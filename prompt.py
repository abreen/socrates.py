from util import *

PROMPT_MODES = [1, '1', '*', '+', '?']

def prompt(choices, mode='*'):
    if mode not in PROMPT_MODES:
        raise ValueError("mode '{}' is invalid".format(mode))

    if len(choices) > 26:
        raise ValueError("too many choices")

    if mode == '*':
        header = "select zero or more:"
        max, min = float('inf'), 0

    elif mode == '+':
        header = "select one or more:"
        max, min = float('inf'), 1

    elif mode in [1, '1']:
        header = "select one:"
        max, min = 1, 1

    elif mode == '?':
        header = "select zero or one:"
        max, min = 1, 0

    letters = list(map(lambda x: chr(ord('a') + x), range(len(choices))))

    num_selections = 0
    selections = []     # unique indices into choices list

    while num_selections < min or num_selections < max:
        sprint(COLOR_GREEN + header + COLOR_RESET)

        for i in range(len(choices)):
            if i in selections:
                sprint(" × {}. {}".format(letters[i], choices[i]))
            else:
                sprint("   {}. {}".format(letters[i], choices[i]))

        try:
            sel = input(COLOR_CYAN + "make a selection (or ! "
                        "to commit): " + COLOR_RESET)
        except KeyboardInterrupt:
            from util import exit, ERR_INTERRUPTED
            print()
            sprint("exiting due to a keyboard interrupt", error=True)
            exit(ERR_INTERRUPTED)

        if sel == '!':
            if num_selections < min:
                sprint("can't stop now; you must make {} {}".format(
                       min, plural("selection", min)), error=True)
                continue
            else:
                break

        try:
            if letters.index(sel) in selections:
                sprint("removing selection of " + sel)
                selections.remove(letters.index(sel))
                continue

            selections.append(letters.index(sel))
            num_selections += 1

        except ValueError:
            if sel == '':
                sprint("make a selection (or ! to commit)", error=True)
            else:
                sprint("invalid selection: not in list", error=True)
            continue

    return selections
