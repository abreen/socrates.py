"""Utility classes to represent criteria for an assignment."""

VALID_TEST_ACTIONS = ['eval',         # evaluate an expression
                      'recursive',    # check for a recursive function or method
                      'output',       # match output of an expression
                      'review']       # pause for human input


class Criteria:
    """Represents requirements for student submissions. Contains one or more
    Module objects which store Function objects, representing required
    parts of a submission. Also contains zero or more Test objects,
    which are used by socrates in grading mode to automate grading tasks.
    """

    def __init__(self, assignment_name, short_name, course_name):
        self.assignment_name = assignment_name      # nice name ("PS 0")
        self.short_name = short_name                # safe for filename ("ps0")
        self.course_name = course_name

        # (<module_name>, <Module object>)
        self.modules = dict()


    def __str__(self):
        return "criteria for {}".format(self.assignment_name)


    def add_module(self, module):
        if module.name in self.modules:
            raise ValueError("a module by this name is already included")

        self.modules[module.name] = module

    def get_total_points(self):
        s = 0
        for m in self.modules.values():
            s += m.get_total_points()

        return s


    def to_dict(self):
        return {'assignment_name': self.assignment_name,
                'short_name': self.short_name,
                'course_name': self.course_name,
                'modules': [m.to_dict() for m in self.modules.values()]}



class Module:
    """Represents a module that the criteria specifies should be in a student's
    submission.
    """

    def __init__(self, module_name, functions=None, tests=None):
        self.name = module_name

        # (<function_name>, <Function object>)
        self.functions = dict() if not functions else functions

        # module-level tests
        self.tests = [] if not tests else tests


    def __str__(self):
        return "module {}".format(self.name)


    def add_function(self, func):
        if func.name in self.functions:
            raise ValueError("a function by this name is already included")

        self.functions[func.name] = func


    def add_test(self, test):
        if type(test.target) is not Module:
            raise ValueError("cannot add test for non-module to module")

        self.tests.append(test)


    def get_total_points(self):
        s = 0
        for f in self.functions.values():
            s += f.point_value

        return s


    def to_dict(self):
        return {'module_name': self.name,
                'functions': [f.to_dict() for f in self.functions.values()],
                'tests': [t.to_dict() for t in self.tests]}



class Function:
    """Represents a function that the criteria specifies should be in a module
    of a student's submission.
    """

    def __init__(self, function_name, parent_module, parameters,
                 point_value, tests=None):
        self.name = function_name
        self.parent_module = parent_module
        self.point_value = point_value
        self.parameters = parameters                # list of strings

        # function-level tests
        self.tests = [] if not tests else tests


    def __str__(self):
        params = ', '.join(self.parameters)
        name = "{}({})".format(self.name, params)
        return "function {}".format(name)


    def add_test(self, test):
        if type(test.target) is not Function:
            raise ValueError("cannot add test for non-function to function")

        self.tests.append(test)


    def to_dict(self):
        return {'function_name': self.name,
                'parameters': self.parameters,
                'point_value': self.point_value,
                'tests': [t.to_dict() for t in self.tests]}



class Test:
    """Represents a test that socrates will run to determine if the student
    should get credit for some part of a submission. A test's "target" is the
    function or module on which it should run. See VALID_TEST_ACTIONS for
    possible test types.
    """

    def __init__(self, action, target, deduction, description,
                 arguments, expected):
        if action not in VALID_TEST_ACTIONS:
            raise ValueError("test action '" + action + "' invalid; choose "
                             "from " + str(VALID_TEST_ACTIONS))

        self.action = action            # e.g., 'eval'
        self.target = target            # Module or Function object to test

        self.deduction = deduction      # num. of points to deduct if test fails
        self.description = description  # deduction reasoning for grade file

        # the 'review' action will not use these, since the deduction will
        # depend on the human grader
        self.arguments = arguments      # for function, what arguments to pass
        self.expected = expected        # expected return value or output


    def __str__(self):
        return "test of {}: {} ({} points)".format(self.target,
               self.description, self.deduction)


    def to_dict(self):
        test_dict = {'action': self.action,
                     'target': str(self.target),
                     'deduction': self.deduction,
                     'description': self.description}

        if self.action != 'review':
            test_dict['arguments'] = self.arguments
            test_dict['expected'] = self.expected

        return test_dict


    def from_dict(dict_obj, test_target):
        """Given a dict representing a Test object (perhaps from decoding
        a JSON file), and the actual Function or Module object that is the
        target of the test, create a new Test object.
        """

        if type(dict_obj) is not dict:
            raise ValueError("dict expected from which to create Test object")

        if not test_target:
            raise ValueError("the target of this test must be specified")

        args = {'action': dict_obj['action'],
                'target': test_target,
                'deduction': dict_obj['deduction'],
                'description': dict_obj['description']}

        if 'arguments' in dict_obj:
            args['arguments'] = dict_obj['arguments']
        else:
            args['arguments'] = None

        if 'expected' in dict_obj:
            args['expected'] = dict_obj['expected']
        else:
            args['expected'] = None

        return Test(**args)
