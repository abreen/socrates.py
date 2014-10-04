import filetypes
from filetypes.plainfile import PlainFile, ReviewTest
from filetypes.basefile import TestSet
from filetypes.basetest import BaseTest

from util import sprint, add_to, COLOR_GREEN, COLOR_YELLOW, COLOR_RESET


class EvalTest(BaseTest):
    yaml_type = 'eval'

    def __init__(self, dict_, file_type):
        super().__init__(dict_, file_type)

        # target could be a PythonFunction or a PythonVariable
        # potentially confusing: this is None initially, but it should be
        # set by the PythonFunction or PythonVariable that
        # initially creates an instance of this object
        self.target = None

        # this test might not have a deduction if it's inside a test set
        if 'deduction' in dict_:
            self.deduction = dict_['deduction']

        # add optional components, if present (except 'arguments' and
        # 'output', which are special and handled below)
        for a in ['input', 'value', 'random_seed']:
            if a in dict_:
                setattr(self, a, dict_[a])
            else:
                setattr(self, a, None)

        self.arguments = []
        if 'arguments' in dict_:
            if type(dict_['arguments']) is list:
                self.arguments = dict_['arguments']
            elif type(dict_['arguments']) is dict:
                for param_name, param_val in dict_['arguments'].items():
                    self.arguments.append((param_name, param_val))
            else:
                raise ValueError("arguments must be in a list or dictionary")

        # store expected output; this may be an exact string or a regex
        if 'output' in dict_:
            if type(dict_['output']) is dict and 'match' in dict_['output']:
                import re
                pattern = re.compile(dict_['output']['match'])
                self.output = {'match': pattern}
            else:
                self.output = dict_['output']
        else:
            self.output = None


    def __str__(self):
        return "eval of {} ({} pts.)".format(self.target,
                                             self.deduction)


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

        if self.random_seed:
            import random
            random.seed(self.random_seed)

        try:
            return_value = eval(fn_call, globals(), {mod_name:context})
        except:
            import sys

            err = sys.exc_info()
            sprint(COLOR_YELLOW + "failing a test due to an "
                   "error ({})".format(err[1]) + COLOR_RESET)
            return {'deduction': self.deduction,
                    'description': self.description,
                    'notes': [str(err[1]) + " (" + str(err[0].__name__) + ")"]}

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
                result['notes'].append("expected value: " + repr(self.value))
                result['notes'].append("produced value: " + repr(return_value))

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
    def __init__(self, dict_, file_type):
        super().__init__(dict_, file_type)

        if 'print_target' in dict_:
            self.print_target = dict_['print_target']
        else:
            self.print_target = True

        # target could be a PythonFile, a PythonFunction or a PythonVariable
        # potentially confusing: this is None initially, but it should be
        # set by the PythonFile, PythonFunction, or PythonVariable that
        # initially creates an instance of this object
        self.target = None


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
            import inspect
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

        else:
            raise ValueError("invalid target for this review test")

        return super().run(temp.name)



class PythonFile(PlainFile):
    yaml_type = 'python'
    extensions = ['py']
    supported_tests = PlainFile.supported_tests.copy()
    supported_tests.append(PythonReviewTest)
    supported_tests.append(EvalTest)


    def __init__(self, dict_):
        super().__init__(dict_)

        self.functions = []
        self.variables = []

        if 'error_deduction' in dict_:
            self.error_deduction = dict_['error_deduction']
        else:
            self.error_deduction = None

        if 'tests' in dict_:
            for t in dict_['tests']:
                test_cls = filetypes.find_test_class(PythonFile.yaml_type,
                                                     t['type'])
                self.tests.append(test_cls(t, PythonFile.yaml_type))

        if 'functions' in dict_:
            for f in dict_['functions']:
                self.functions.append(PythonFunction(f))

        if 'variables' in dict_:
            for v in dict_['variables']:
                self.variables.append(PythonVariable(v))

        # set target of tests for module to this new PythonFile object
        for test in self.tests:
            test.target = self

        if 'point_value' in dict_:
            self.point_value = dict_['point_value']
        else:
            self.point_value = sum([f.point_value for f in self.functions]) + \
                               sum([v.point_value for v in self.variables])


    def run_tests(self):
        import sys
        import io
        import os

        results = dict()
        results[self] = []

        actual_setrecursionlimit = sys.setrecursionlimit

        def intercept_stacksize_change(new_val):
            sprint("intercepting call to sys.setrecursionlimit()")
            old_val = sys.getrecursionlimit()
            if new_val < old_val:
                sprint("keeping stack size at " + str(old_val))
                return
            else:
                sprint("growing stack size to " + str(new_val))
                actual_setrecursionlimit(new_val)

        sys.setrecursionlimit = intercept_stacksize_change

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

            if self.error_deduction:
                deduction = self.error_deduction
            else:
                deduction = self.point_value

            sprint(COLOR_YELLOW + "deducting {} points for error during "
                   "import".format(deduction) + COLOR_RESET)

            return [{'deduction': deduction,
                     'description': "error importing '{}'".format(self.path),
                     'notes': ["encountered {}".format(err[0].__name__)]}]

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

    def __init__(self, dict_):
        self.name = dict_['function_name']
        self.parameters = dict_['parameters']
        self.point_value = dict_['point_value']

        self.tests = []
        if 'tests' in dict_:
            for t in dict_['tests']:
                test_cls = filetypes.find_test_class(PythonFile.yaml_type,
                                                     t['type'])
                self.tests.append(test_cls(t, PythonFile.yaml_type))

        # set target of tests for module to this new PythonFunction object
        for test in self.tests:
            test.target = self


    def __str__(self):
        if self.parameters:
            params = ', '.join(self.parameters)
        else:
            params = ""

        name = "{}({})".format(self.name, params)
        return "function {}".format(name)



class PythonVariable:
    """Utility class representing a Python variable that the criteria specifies
    should be in a module of a student's submission. Used only with files of
    type 'python'.
    """

    def __init__(self, dict_):
        self.name = dict_['variable_name']
        self.point_value = dict_['point_value']

        self.tests = []
        if 'tests' in dict_:
            for t in dict_['tests']:
                test_cls = filetypes.find_test_class(PythonFile.yaml_type,
                                                     t['type'])
                self.tests.append(test_cls(t, PythonFile.yaml_type))

        # set target of tests for module to this new PythonVariable object
        for test in self.tests:
            test.target = self


    def __str__(self):
        return "variable {}".format(self.name)


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
