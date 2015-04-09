"""Useful functions for custom scripts."""


def call_and_trace_files(func, files, *args, **kwargs):
    """Given a function, a reference to a list, and any arguments
    to the function followed by any keyword arguments to the
    function, call the function with the arguments and fill the
    referenced list with a list of files opened for writing
    by the function or any function it calls. The return value
    of the given function is returned.
    """
    import builtins
    old_open = builtins.open

    def open_wrapper(*args2, **kwargs2):
        mode = 'r'
        if len(args2) > 1:
            mode = args2[1]
        elif 'mode' in kwargs2:
            mode = kwargs2['mode']

        if mode and ('w' in mode or 'x' in mode or \
                     'a' in mode or mode == 'w+b'):
            files.append(args2[0])

        return old_open(*args2, **kwargs2)

    builtins.open = open_wrapper
    rv = func(*args, **kwargs)
    builtins.open = old_open
    return rv
