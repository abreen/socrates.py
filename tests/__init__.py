__all__ = ['basetest', 'evaltest', 'reviewtest', 'testset']

from tests import basetest
from tests import *


_test_handlers = dict()
for cls in basetest.BaseTest.__subclasses__():
    _test_handlers[cls.handles_type] = cls


def get_test_class(test_type):
    """Given a test type specified by a criteria file, find the appropriate
    subclass of BaseTest that handles tests of that type. The class is
    returned, or ValueError is raised if the test type is not supported.
    """

    if test_type in _test_handlers:
        return _test_handlers[test_type]
    else:
        raise ValueError("unsupported test type '{}'".format(test_type))

