"""Utility classes to represent criteria for an assignment."""

VALID_TEST_TYPES = ['eval',         # evaluate an expression
                    'recursive',    # check for a recursive function or method
                    'output',       # match output of an expression
                    'review']       # pause for human input


class Criteria:
    """Represents requirements for student submissions. Contains one or more
    ExpectedModule objects, which store ExpectedFunction objects. Also contains
    zero or more Test objects, which can automate grading tasks.
    """

    def __init__(self, name):
        self.assignment_name = name
        self.total_points = None
        self.modules = []


    def add_module(self, module):
        self.modules.append(module)



class ExpectedModule:
    """Represents a module that should be part of a student's submission.
    Contains ExpectedFunction objects, and tests that can be run to evaluate
    the behavior of those functions, and take any necessary deductions.
    """

    def __init__(self, name, funcs=None, tests=None):
        self.module_name = name

        if not tests:
            self.tests = []
        else:
            self.tests = tests

        if not funcs:
            self.required_functions = []
        else:
            self.required_functions = funcs


    def add_function(self, func):
        self.required_functions.append(func)


    def has_function(self, func):
        for f in self.required_functions:
            if f.function_name == func:
                return True

        return False


    def add_test(self, test):
        if test.target == 'function' and not self.has_function(test.name):
            raise ValueError("test target not in module's required functions")

        self.tests.append(test)



class ExpectedFunction:

    def __init__(self, name, params=None, value=None):
        self.function_name = name
        self.point_value = value

        if not params:
            self.parameters = []
        else:
            self.parameters = params



class Test:

    def __init__(self, test_type, target, name, args=None, expected=None,
                 deduction=None, desc=None):

        if test_type not in VALID_TEST_TYPES:
            raise ValueError("test type '" + str(test_type) + "' invalid")

        if test_type != 'review' and not deduction:
            raise ValueError("a non-review test must have a deduction")

        self.test_type = test_type
        self.target = target
        self.name = name

        self.arguments= args
        self.expected = expected

        self.deduction = deduction
        self.description = desc

