"""Various utility functions."""


def sprint(string, error=False):
    import sys

    if error:
        print("socrates: error: " + string, file=sys.stderr)
    else:
        print("socrates: " + string, file=sys.stdout)
