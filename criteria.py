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



class ExpectedModule:
    """Represents a module that should be part of a student's submission.
    Contains ExpectedFunction objects, and tests that can be run to evaluate
    the behavior of those functions, and take any necessary deductions.
    """

    def __init__(self, name=None, funcs=None, tests=None):
        self.module_name = name
        self.tests = tests

        if not funcs:
            self.required_functions = []
        else:
            self.required_functions = funcs


    def add_function(self, func):
        self.required_functions.append(func)



class ExpectedFunction:

    def __init__(self, name=None, params=None, value=None):
        self.function_name = name
        self.point_value = value

        if not params:
            self.parameters = []
        else:
            self.parameters = params



class Test:

    def __init__(self, test_type, args, expected_value, points, description):
        if test_type not in VALID_TEST_TYPES:
            raise ValueError("test type '" + str(test_type) + "' invalid")

        self.test_type = test_type
        self.actual_arguments = args
        self.expected_value = expected_value

        self.deduction = points
        self.description = description


