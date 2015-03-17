class LogisimError(Exception):
    def __init__(self, str_=None):
        if str_:
            Exception.__init__(self, str_)
        else:
            Exception.__init__(self)

class NoInputsError(LogisimError):
    pass

class TooManyInputsError(LogisimError):
    pass

class NoSuchPinLabelError(LogisimError):
    pass

class NoValueGivenError(LogisimError):
    pass
