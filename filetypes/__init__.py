__all__ = ['basefile', 'plainfile', 'pythonfile']

from filetypes import basefile
from filetypes import basetest
from filetypes import *


def _traverse_subclasses(cls, classes):
    """Given a root class object (any subclass of BaseFile or BaseTest) and a
    dictionary, add this class and all its subclasses to the dictionary, using
    the json_type attribute as a key. Raise ImportError if two classes try to
    handle the same json_type.
    """
    if cls.json_type in classes:
        raise ImportError("two or more classes handling the same "
                          "type (type '{}')".format(cls.json_type))

    classes[cls.json_type] = cls

    for subcls in cls.__subclasses__():
        _traverse_subclasses(subcls, classes)


_file_handlers = dict()
for subcls in basefile.BaseFile.__subclasses__():
    _traverse_subclasses(subcls, _file_handlers)

_test_handlers = dict()
for subcls in basetest.BaseTest.__subclasses__():
    _traverse_subclasses(subcls, _test_handlers)


def find_file_class(file_type):
    """Given a file type specified by a criteria file, find the appropriate
    subclass of BaseFile that can handle that type. The class is returned, or
    ValueError is raised if the file type is not supported.
    """

    if file_type in _file_handlers:
        return _file_handlers[file_type]
    else:
        raise ValueError("unsupported file type '{}'".format(file_type))


def find_test_class(test_type):
    """Given a test type specified by a criteria file, find the appropriate
    subclass of BaseTest that implements the test. The class is returned, or
    ValueError is raised if the test type is not supported.
    """

    if test_type in _test_handlers:
        return _test_handlers[test_type]
    else:
        raise ValueError("unsupported test type '{}'".format(test_type))
