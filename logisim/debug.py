suppress_narration = []

def narrate(func):
    def inner(*args, **kwargs):
        func_string = _func_string(func.__name__, args, kwargs)

        if len(suppress_narration) == 0:
            print(func_string + ": called")

        rval = func(*args, **kwargs)

        if len(suppress_narration) == 0:
            print(func_string + ": returning " + repr(rval))
        return rval

    return inner


def _func_string(name, args, kwargs):
    args_str = ', '.join([repr(x) for x in args])
    s = name + "(" + args_str
    if kwargs:
        kwargs_str = ', '.join([k + "=" + repr(v) for k, v in kwargs.items()])
        s += ", " + kwargs_str

    return s + ")"
