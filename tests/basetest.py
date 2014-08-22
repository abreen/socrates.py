from abc import ABCMeta, abstractmethod


class BaseTest:
    """Represents a test that socrates will run to determine if the student
    should get credit for some part of a submission. A test's "target" is the
    function or module on which it should run.
    """
    __metaclass__ = ABCMeta

    # this data member should be set by extenders so that socrates can locate
    # the appropriate Test subclass to instantiate when reading a criteria file
    handles_type = None


    # this constructor represents the minimal requirements of a Test object
    # in terms of its attributes --- if subclasses override this constructor,
    # they should make sure their classes have at least these attributes,
    # since the socrates code depends on them
    def __init__(self, target, description, deduction):
        self.target = target
        self.description = description
        self.deduction = deduction

    
    @staticmethod
    @abstractmethod
    def from_dict(dict_obj, target):
        """Given a dictionary (the result of decoding the JSON object from
        a criteria file) and a target (a Module or Function object representing
        the expected target of the test), return an instance of the Test
        subclass whose run_test() method can then be invoked to run the test.
        """
        raise NotImplementedError()


    @abstractmethod
    def to_dict(self):
        """Return a dictionary representation of this test, compliant with
        the JSON object specification.
        """
        raise NotImplementedError()


    @abstractmethod
    def run_test(self, actual_target, context):
        """Given the actual target of a test (e.g., an imported function
        object) and a context (the imported module object resulting from
        importing a student's submission), test the submission and return
        True if the test passes or False if the test fails.
        """
        raise NotImplementedError()


    def __str__(self):
        return "'{}' test of {}".format(self.handles_type, self.target)
