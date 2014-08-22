import sys
import io

from tests import basetest


class EvalTest(basetest.BaseTest):
    handles_type = 'eval'

    def __init__(self, target, description, deduction,
                 arguments=None, input=None, value=None, output=None):
        if arguments and type(arguments) is not dict:
            raise ValueError("arguments must be a dictionary containing "
                             "<arg-name>: <arg-value> pairs")

        super().__init__(target, description, deduction)

        # optional components
        self.arguments = arguments      # what arguments to pass (dict)
        self.input = input              # what input to send
        self.value = value              # expected return value
        self.output = output            # expected output


    def __str__(self):
        return "evaluation test of {}: {} ({} points)".format(self.target,
                                                              self.description,
                                                              self.deduction)


    def to_dict(self):
        test_dict = {'type': self.handles_type,
                     'description': self.description,
                     'deduction': self.deduction,
                     'arguments': self.arguments,
                     'input': self.input,
                     'value': self.value,
                     'output': self.output}

        return test_dict


    @staticmethod
    def from_dict(dict_obj, test_target):
        if not test_target:
            raise ValueError("the target of this test must be specified")

        args = {'target': test_target,
                'description': dict_obj['description'],
                'deduction': dict_obj['deduction']}

        # add optional components, if present
        for a in ['arguments', 'input', 'value', 'output']:
            if a in dict_obj:
                args[a] = dict_obj[a]

        return EvalTest(**args)


    @staticmethod
    def __format_args(args):
        """Return a string that, when placed inside of calling parentheses
        and eval()'d, should call the function with the appropriate arguments.
        """

        if type(args) is dict:
            args = ["{}={}".format(k, v) for (k, v) in args.items()]

        return ', '.join(args)


    def run_test(self, actual_target, context):
        # TODO run eval in separate thread
        mod_name = self.target.parent_module.name
        name = self.target.name

        if self.arguments:
            formatted_args = EvalTest.__format_args(self.arguments)
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

