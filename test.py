from criteria import *

VALID_TEST_ACTIONS = ['eval',         # evaluate an expression
                      'recursive',    # check for a recursive function or method
                      'output',       # match output of an expression
                      'review']       # pause for human input

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
