import sys
import inspect
from io import StringIO         # for capturing standard out

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


    @staticmethod
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


    @staticmethod
    def __format_args(args):
        """Return a string that, when placed inside of calling parentheses
        and eval()'d, should call the function with the appropriate arguments.
        """

        if type(args) is dict:
            args = ["{}={}".format(k, v) for (k, v) in args.items()]

        return ', '.join(args)


    def run_test(self, actual_target, context):
        """Given an actual target (the Python function or module object
        created by an import of the student's code) and a module context
        (the module object created by an import of the student's code),
        attempt to run this test on the target. Return True if the student
        submission contains code that passes this test, or False if it
        fails the test. The context may not actually be used, if the test
        can be performed without using eval().
        """

        if type(actual_target) is Module:
            # TODO implement testing for modules
            return True

        if self.action in ['eval', 'output']:
            return self.__run_eval_output(actual_target, context)
        elif self.action == 'review':
            return self.__run_review(actual_target)
        elif self.action == 'recursive':
            return True
        else:
            raise ValueError("test has invalid action")


    def __run_eval_output(self, actual_target, context):
        """Perform an 'eval' or 'output' test by creating a function call
        string and passing it to eval() with the local module context.
        Return True iff the expected value or output is produced.
        """

        mod_name = self.target.parent_module.name
        name = self.target.name
        formatted_args = Test.__format_args(self.arguments)
        call = "{}.{}({})".format(mod_name, name, formatted_args)

        if self.action == 'eval':
            result = eval(call, globals(), {mod_name:context})
            return result == self.expected

        elif self.action == 'output':
            old_stdout = sys.stdout
            output = StringIO()
            sys.stdout = output

            eval(call, globals(), {mod_name:context})

            sys.stdout = old_stdout

            return output.getvalue() == self.expected


    def __run_review(self, actual_target):
        """Perform a 'review' test by acquring the source code of the function
        and printing it. A human is asked to confirm the deduction.
        """

        print(inspect.getsource(actual_target))
        print("Deduction description: {}".format(self.description))
        print("Deduction value: {}".format(self.deduction))

        while True:
            ans = input("Should this deduction be taken (yes/no)? ")

            if ans in ['yes', 'no']:
                break

        if ans == 'yes':
            return False
        else:
            return True
