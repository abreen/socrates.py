import sys
import inspect
import io

from criteria import *

VALID_TEST_TYPES = ['eval',         # evaluate an expression
                    'review']       # pause for human input

class Test:
    """Represents a test that socrates will run to determine if the student
    should get credit for some part of a submission. A test's "target" is the
    function or module on which it should run. See VALID_TEST_TYPES for
    possible test types.
    """

    def __init__(self, test_type, target, description, deduction,
                 arguments=None, input=None, value=None, output=None):
        if test_type not in VALID_TEST_TYPES:
            raise ValueError("test type '" + test_type + "' invalid; choose "
                             "from " + str(VALID_TEST_TYPES))

        if arguments and type(arguments) is not dict:
            raise ValueError("arguments must be a dictionary containing "
                             "<arg-name>: <arg-value> pairs")

        # required components
        self.type = test_type           # e.g., 'eval'
        self.target = target            # Module or Function object to test
        self.description = description  # deduction reasoning for grade file
        self.deduction = deduction      # num. of points to deduct if test fails

        # optional components
        self.arguments = arguments      # what arguments to pass (dict)
        self.input = input              # what input to send
        self.value = value              # expected return value
        self.output = output            # expected output


    def __str__(self):
        return "test of {}: {} ({} points)".format(self.target,
                                                   self.description,
                                                   self.deduction)


    def to_dict(self):
        test_dict = {'type': self.type,
                     'description': self.description,
                     'deduction': self.deduction,
                     'arguments': self.arguments,
                     'input': self.input,
                     'value': self.value,
                     'output': self.output}

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

        args = {'test_type': dict_obj['type'],
                'target': test_target,
                'description': dict_obj['description'],
                'deduction': dict_obj['deduction']}

        # add optional components, if present
        for a in ['arguments', 'input', 'value', 'output']:
            if a in dict_obj:
                args[a] = dict_obj[a]

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

        # TODO run tests in separate thread

        if type(actual_target) is Module:
            # TODO implement testing for modules
            return True

        if self.type == 'eval':
            return self.__run_eval(actual_target, context)
        elif self.type == 'review':
            return self.__run_review(actual_target)
        else:
            raise ValueError("test has invalid type")


    def __run_eval(self, actual_target, context):
        """Perform an 'eval' test by creating a function call string and
        passing it to eval() with the local module context.
        Return True iff the expected value or output is produced given
        the input and/or arguments specified by the test.
        """

        mod_name = self.target.parent_module.name
        name = self.target.name

        if self.arguments:
            formatted_args = Test.__format_args(self.arguments)
        else:
            formatted_args = ""

        fn_call = "{}.{}({})".format(mod_name, name, formatted_args)

        if self.input:
            in_buf = io.StringIO(self.input)
            sys.stdin = in_buf

        if self.output:
            out_buf = io.StringIO()
            sys.stdout = out_buf

        return_value = eval(fn_call, globals(), {mod_name:context})

        # restore default standard in/out
        sys.stdin, sys.stdout = sys.__stdin__, sys.__stdout__

        passed = True
        if self.value:
            passed = passed and self.value == return_value
        if self.output:
            passed = passed and self.output == out_buf.getvalue()

        return passed


    def __run_review(self, actual_target):
        """Perform a 'review' test by acquring the source code of the function
        and printing it. A human is asked to confirm the deduction.
        """

        print(inspect.getsource(actual_target))
        print("Deduction description: {}".format(self.description))
        print("Deduction value: {}".format(self.deduction))

        while True:
            ans = input("Should this deduction be taken (y/n)? ")

            if ans in ['y', 'n', 'yes', 'no']:
                break

        if ans == 'y' or ans == 'yes':
            # the deduction *should* be taken, therefore this test fails
            return False
        else:
            # the deduction *should not* be taken, therefore this test passes
            return True

