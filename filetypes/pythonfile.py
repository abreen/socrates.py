import filetypes
from filetypes.plainfile import PlainFile, ReviewTest
from filetypes.basefile import TestSet
from filetypes.basetest import BaseTest

from util import sprint, add_to, COLOR_GREEN, COLOR_RESET


class EvalTest(BaseTest):
    json_type = 'eval'

    def __init__(self, target, description, deduction=None,
                 arguments=None, input=None, value=None, output=None):
        self.target = target
        self.description = description

        self.deduction = deduction

        self.arguments = []
        if type(arguments) is list:
            self.arguments = arguments
        elif type(arguments) is dict:
            for param_name, param_val in arguments.items():
                self.arguments.append((param_name, param_val))
        else:
            raise ValueError("arguments must be in a list or dictionary")

        self.input = input              # what input to send
        self.value = value              # expected return value

        # get expected output; this may be an exact string or a regex
        if type(output) is dict and 'match' in output:
            import re
            pattern = re.compile(output['match'])
            self.output = {'match': pattern}
        else:
            self.output = output


    def __str__(self):
        return "eval of {} ({} pts.)".format(self.target,
                                             self.deduction)


    @staticmethod
    def from_dict(dict_obj, file_type):
        args = {'target': None,
                'description': dict_obj['description']}

        # this test might not have a deduction if it's inside a test set
        if 'deduction' in dict_obj:
            args['deduction'] = dict_obj['deduction']

        # add optional components, if present
        for a in ['arguments', 'input', 'value', 'output']:
            if a in dict_obj:
                args[a] = dict_obj[a]

        return EvalTest(**args)


    def run(self, cxt):
        if type(self.target) is PythonFunction:
            return self.__run_function(cxt)
        elif type(self.target) is PythonVariable:
            return self.__run_variable(cxt)
        elif type(self.target) is PythonFile:
            return self.__run_module(cxt)
        else:
            raise ValueError("invalid target type")


    def __run_function(self, context):
        import sys
        import io

        mod_name = context.__name__
        fn_name = self.target.name

        formatted_args = self.__format_args(context)

        fn_call = "{}.{}({})".format(mod_name, fn_name, formatted_args)

        if self.input:
            in_buf = io.StringIO(self.input)
            sys.stdin = in_buf

        if self.output:
            out_buf = io.StringIO()
            sys.stdout = out_buf

        try:
            return_value = eval(fn_call, globals(), {mod_name:context})
        except AttributeError as err:
            return {'deduction': self.deduction,
                    'description': self.description,
                    'notes': [str(err)]}

        # restore default standard in/out
        sys.stdin, sys.stdout = sys.__stdin__, sys.__stdout__

        if self.output is not None:
            output = out_buf.getvalue()

        passed = True
        if self.value is not None:
            passed = passed and self.value == return_value
        if self.output is not None:
            passed = passed and self.__output_matches(output)

        if passed:
            return None
        else:
            result =  {'deduction': self.deduction,
                       'description': self.description,
                       'notes': []}

            if self.value is not None:
                result['notes'].append("expected value: " + str(self.value))
                result['notes'].append("produced value: " + str(return_value))

            if self.output is not None and type(self.output) is str:
                import util
                eo, po = util.escape(self.output), util.escape(output)

                result['notes'].append("expected output: " + eo)
                result['notes'].append("produced output: " + po)

            return result


    def __format_args(self, cxt):
        if self.arguments:
            # the student may have chosen different names for their function's
            # parameters; we must create a mapping from the names in the
            # criteria to the names in the submission
            if type(self.arguments[0]) is tuple:
                from inspect import signature

                func_obj = _find_function_from_cxt(cxt, self.target.name)
                student_param_names = list(signature(func_obj).parameters)
                altered_args = []

                # for each parameter in the criteria
                for i in range(len(self.target.parameters)):
                    # find the index of argument value from the eval test
                    for j in range(len(self.arguments)):
                        if self.arguments[j][0] == self.target.parameters[i]:
                            break

                    # val holds the value of this parameter from the eval test
                    val = self.arguments[j][1]

                    # add this value with the student-given name
                    altered_args.append((student_param_names[i], val))

                args = ["{}={}".format(k, repr(v)) for (k, v) in altered_args]
                return ', '.join(args)
            else:
                # will not use keyword arguments, just positional
                return ', '.join(self.arguments)
        else:
            # function takes no arguments
            return ''


    def __run_variable(self, context):
        import sys
        import io

        mod_name = context.__name__
        var_name = self.target.name
        exp = mod_name + "." + var_name

        try:
            value = eval(exp, globals(), {mod_name:context})
        except AttributeError as err:
            return {'deduction': self.deduction,
                    'description': self.description,
                    'notes': [str(err)]}

        if value == self.value:
            return None
        else:
            result = {'deduction': self.deduction,
                      'description': self.description,
                      'notes': []}

            result['notes'].append("expected value: " + str(self.value))
            result['notes'].append("produced value: " + str(value))

            return result


    def __run_module(self, context):
        import sys
        import io
        import imp

        if self.input:
            in_buf = io.StringIO(self.input)
            sys.stdin = in_buf

        if self.output:
            out_buf = io.StringIO()
            sys.stdout = out_buf

        imp.reload(context)

        # restore default standard in/out
        sys.stdin, sys.stdout = sys.__stdin__, sys.__stdout__

        if self.output is not None:
            output = out_buf.getvalue()

        passed = True
        if self.output is not None:
            passed = passed and self.__output_matches(output)

        if passed:
            return None
        else:
            result =  {'deduction': self.deduction,
                       'description': self.description,
                       'notes': []}

            if self.output is not None and type(self.output) is str:
                import util
                eo, po = util.escape(self.output), util.escape(output)

                result['notes'].append("expected output: " + eo)
                result['notes'].append("produced output: " + po)

            return result


    def __output_matches(self, out_string):
        """Given a string obtained from the running of a function or
        module, determine whether the output matches the expected output.
        This method handles the case where the criteria file specified
        exact output or a regular expression.
        """

        if type(self.output) is str:
            return self.output == out_string

        if 'match' in self.output:
            import re
            return self.output['match'].match(out_string)

        # TODO this might be a bad idea
        if 'prompt' in self.output:
            sprint("deduction description: {}".format(self.description))
            sprint("deduction value: {}".format(self.deduction))

            ans = input("should this deduction be taken? (y/yes/n/no) ")

            if ans in ['y', 'yes']:
                return {'deduction': self.deduction,
                        'description': self.description,
                        'notes': ["failed human review"]}
            else:
                sprint("taking no deduction")




class PythonReviewTest(ReviewTest):
    def __init__(self, target, description, deduction, print_target=True):
        super().__init__(description, deduction)

        # target can be a PythonFile or PythonFunction
        # TODO this is None initially (confusing)
        self.target = target

        self.print_target = print_target


    @staticmethod
    def from_dict(dict_obj, file_type):
        args = {'description': dict_obj['description'],
                'deduction': dict_obj['deduction'],
                'target': None}

        if 'print_target' in dict_obj:
            args['print_target'] = dict_obj['print_target']

        return PythonReviewTest(**args)


    def run(self, context):
        """Perform a 'review' test by acquring the source code of the function
        or module and printing it. The context is not used. A human is asked
        to confirm the deduction(s).
        """
        from tempfile import NamedTemporaryFile
        temp = NamedTemporaryFile()

        if type(self.target) is PythonFile:
            if self.print_target:
                temp.write(open(self.target.path, 'rb').read())
                temp.flush()

        elif type(self.target) is PythonFunction:
            func_obj = _find_function_from_cxt(context, self.target.name)

            if not func_obj:
                return {'deduction': self.deduction,
                        'description': self.description,
                        'notes': ["could not find {}".format(self.target)]}

            if self.print_target:
                temp.write(inspect.getsource(func_obj).encode('utf-8'))
                temp.flush()

        elif type(self.target) is PythonVariable:
            import inspect
            import re

            mod_src = inspect.getsource(context)

            # TODO find a better way to do this
            pat = re.compile("\s*" + self.target.name + "\s*=")

            for line in mod_src.split('\n'):
                if re.match(pat, line):
                    var_src = line
                    break
            else:
                return {'deduction': self.deduction,
                        'description': self.description,
                        'notes': ["could not find {}".format(self.target)]}

            if self.print_target:
                temp.write((var_src + '\n').encode('utf-8'))
                temp.flush()


        return super().run(temp.name)



class PythonFile(PlainFile):
    json_type = 'python'
    extensions = ['py']
    supported_tests = PlainFile.supported_tests.copy()
    supported_tests.append(PythonReviewTest)
    supported_tests.append(EvalTest)


    def __init__(self, path, point_value=0, tests=None, functions=None, variables=None):
        self.path = path
        self.tests = tests if tests else []
        self.functions = functions if functions else []
        self.variables = variables if variables else []

        if point_value:
            self.point_value = point_value
        else:
            self.point_value = sum([f.point_value for f in self.functions]) + \
                               sum([v.point_value for v in self.variables])


    @staticmethod
    def from_dict(dict_obj):
        args = {'path': dict_obj['path'],
                'tests': [],
                'functions': [],
                'variables': []}

        if 'point_value' in dict_obj:
            args['point_value'] = dict_obj['point_value']

        if 'tests' in dict_obj:
            for t in dict_obj['tests']:
                test_cls = filetypes.find_test_class(PythonFile.json_type, t['type'])
                args['tests'].append(test_cls.from_dict(t, PythonFile.json_type))

        if 'functions' in dict_obj:
            for f in dict_obj['functions']:
                args['functions'].append(PythonFunction.from_dict(f))

        if 'variables' in dict_obj:
            for v in dict_obj['variables']:
                args['variables'].append(PythonVariable.from_dict(v))


        # set target of tests for module to this new PythonFile object
        new = PythonFile(**args)
        for test in new.tests:
            test.target = new

        return new


    def to_dict(self):
        return {'path': self.path,
                'type': self.json_type,
                'point_value': self.point_value,
                'tests': [t.to_dict() for t in self.tests],
                'functions': [f.to_dict() for f in self.functions]}


    def run_tests(self):
        import sys
        import io
        import os

        results = dict()
        results[self] = []

        try:
            directory, name = os.path.split(self.path)
            mod_name = name[:name.index('.py')] if '.py' in name else name

            sys.path.append(directory)

            sprint(COLOR_GREEN + "importing module '{}'".format(mod_name) + \
                   COLOR_RESET)

            # redirect standard out to empty buffer to "mute" the program
            #sys.stdout = io.StringIO()
            module_context = __import__(mod_name)
            #sys.stdout = sys.__stdout__

            sprint(COLOR_GREEN + "finished importing "
                   "module".format(mod_name) + COLOR_RESET)

        except:
            # "un-mute" the program and give socrates access to stdout
            #sys.stdout = sys.__stdout__

            import traceback

            err = sys.exc_info()

            sprint("encountered an error importing "
                   "'{}' module ({})".format(mod_name, err[0].__name__))

            traceback.print_exc()

            return [{'deduction': self.point_value,
                     'description': "error importing '{}'".format(self.path),
                     'notes': ["encountered error {}".format(err[0].__name__)]}]

        found_functions = self.__get_members(module_context, 'functions')
        found_variables = self.__get_members(module_context, 'variables')

        for test in self.tests:
            result = test.run(module_context)
            if result is not None:
                add_to(result, results[self])

        for func in self.functions:
            results[func] = []
            if func not in found_functions:
                results[func].append({'deduction': func.point_value,
                                      'description': "missing function "
                                                     "'{}'".format(func)})
                continue

            for test in func.tests:
                # TODO fix this hacky thing
                if type(test) is TestSet:
                    for m in test.members:
                        m.target = func

                result = test.run(module_context)
                if result is not None:
                    add_to(result, results[func])

        for var in self.variables:
            results[var] = []
            if var not in found_variables:
                results[var].append({'deduction': var.point_value,
                                     'description': "missing variable "
                                                    "'{}'".format(var)})
                continue

            for test in var.tests:
                # TODO fix this hacky thing
                if type(test) is TestSet:
                    for m in test.members:
                        m.target = var

                result = test.run(module_context)
                if result is not None:
                    add_to(result, results[var])

        for target, failures in results.items():
            sum = 0
            for f in failures:
                sum += f['deduction']

                if sum > target.point_value:
                    f['deduction'] = 0

        return [item for subl in results.values() for item in subl]



    def __get_members(self, cxt, kind):
        import inspect
        members = []

        if kind == 'functions':
            for m in inspect.getmembers(cxt, inspect.isfunction):
                for f in self.functions:
                    if f.name == m[0]:
                        members.append(f)

        elif kind == 'variables':
            import types
            bad_types = [types.FunctionType, types.LambdaType, types.MethodType,
                         types.ModuleType]
            for m in inspect.getmembers(cxt):
                if type(m[1]) in bad_types:
                    continue

                for v in self.variables:
                    if v.name == m[0]:
                        members.append(v)

        return members


    def __str__(self):
        return self.path + " (Python file)"



class PythonFunction:
    """Utility class representing a Python function that the criteria specifies
    should be in a module of a student's submission. Used only with files of
    type 'python'.
    """

    def __init__(self, name, parameters, point_value, tests=None):
        self.name = name
        self.parameters = parameters                # list of strings
        self.point_value = point_value

        # function-level tests
        self.tests = [] if not tests else tests


    def __str__(self):
        if self.parameters:
            params = ', '.join(self.parameters)
        else:
            params = ""

        name = "{}({})".format(self.name, params)
        return "function {}".format(name)


    @staticmethod
    def from_dict(dict_obj):
        args = {'name': dict_obj['function_name'],
                'parameters': dict_obj['parameters'],
                'point_value': dict_obj['point_value'],
                'tests': []}

        if 'tests' in dict_obj:
            for t in dict_obj['tests']:
                test_cls = filetypes.find_test_class(PythonFile.json_type, t['type'])
                args['tests'].append(test_cls.from_dict(t, PythonFile.json_type))

        # set target of tests for module to this new PythonFunction object
        new = PythonFunction(**args)
        for test in new.tests:
            test.target = new

        return new


    def to_dict(self):
        return {'function_name': self.name,
                'parameters': self.parameters,
                'point_value': self.point_value,
                'tests': [t.to_dict() for t in self.tests]}



class PythonVariable:
    """Utility class representing a Python variable that the criteria specifies
    should be in a module of a student's submission. Used only with files of
    type 'python'.
    """

    def __init__(self, name, point_value, tests=None):
        self.name = name
        self.point_value = point_value

        # variable-level tests
        self.tests = [] if not tests else tests


    def __str__(self):
        return "variable {}".format(self.name)


    @staticmethod
    def from_dict(dict_obj):
        args = {'name': dict_obj['variable_name'],
                'point_value': dict_obj['point_value'],
                'tests': []}

        if 'tests' in dict_obj:
            for t in dict_obj['tests']:
                test_cls = filetypes.find_test_class(PythonFile.json_type, t['type'])
                args['tests'].append(test_cls.from_dict(t, PythonFile.json_type))

        # set target of tests for module to this new PythonVariable object
        new = PythonVariable(**args)
        for test in new.tests:
            test.target = new

        return new


    def to_dict(self):
        return {'variable_name': self.name,
                'point_value': self.point_value,
                'tests': [t.to_dict() for t in self.tests]}



def _find_function_from_cxt(context, name):
    from inspect import getmembers, isfunction

    for m in getmembers(context, isfunction):
        if m[0] == name:
            return m[1]

    return None
