__all__ = ['basefile', 'plainfile', 'pythonfile', 'picobotfile',
           'logisimfile']

from filetypes import basefile
from filetypes import basetest
from filetypes import *


def _traverse(cls):
    """Given a root class object (any subclass of BaseFile), add this class to
    the _file_handlers dictionary and its subclasses, recursively. For each
    test type that the file type supports, add it to the _test_handlers
    dictionary, keyed by a (file type YAML keyword, test type YAML keyword) pair.
    """
    _file_handlers[cls.yaml_type] = cls

    for t in cls.supported_tests:
        _test_handlers[(cls.yaml_type, t.yaml_type)] = t

    for subcls in cls.__subclasses__():
        _traverse(subcls)


_file_handlers = dict()
_test_handlers = dict()
for subcls in basefile.BaseFile.__subclasses__():
    _traverse(subcls)


def find_file_class(file_type):
    """Given a file type specified by a criteria file, find the appropriate
    subclass of BaseFile that can handle that type. The class is returned, or
    ValueError is raised if the file type is not supported.
    """
    try:
        return _file_handlers[file_type]
    except KeyError:
        raise ValueError("unsupported file type '{}'".format(file_type))


def find_test_class(file_type, test_type):
    """Given a test type specified by a criteria file, find the appropriate
    subclass of BaseTest that implements the test. The class is returned, or
    ValueError is raised if the test type is not supported.
    """
    try:
        return _test_handlers[(file_type, test_type)]
    except KeyError:
        raise ValueError("unsupported test type '{}'".format(test_type))
