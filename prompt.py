import util

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
    selections = []         # unique indices into choices list

    while num_selections < min or num_selections < max:
        util.print(util.green(header))

        for i in range(len(choices)):
            if i in selections:
                choice = " × "
            else:
                choice = "   "

            choice += str(letters[i]) + '. ' + str(choices[i])

            if i in selections:
                choice = util.yellow(choice)

            util.print(choice)

        try:
            sel = input(util.green("make a selection (or ! to commit): "))
        except KeyboardInterrupt:
            util.exit(util.ERR_INTERRUPTED)

        if sel == '!':
            if num_selections < min:
                util.error("can't stop now; you must make "
                           "{} {}".format(min,
                                          util.plural("selection", min)))
                continue
            else:
                break

        try:
            if letters.index(sel) in selections:
                selections.remove(letters.index(sel))
                continue

            selections.append(letters.index(sel))
            num_selections += 1

        except ValueError:
            if sel == '':
                util.print("make a selection (or ! to commit)")
            else:
                util.error("invalid selection: not in list")
            continue

    return selections
