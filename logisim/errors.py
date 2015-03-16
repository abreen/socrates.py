class LogisimError(Exception):
    pass

class NoInputsError(LogisimError):
    pass

class TooManyInputsError(LogisimError):
    pass

class NoSuchPinLabelError(LogisimError):
    pass
