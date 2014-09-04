import filetypes
from filetypes.plainfile import PlainFile
from filetypes.basefile import TestSet
from filetypes.basetest import BaseTest


class EvalTest(BaseTest):
    json_type = 'eval'

    def __init__(self, target, description, deduction=None,
                 arguments=None, input=None, value=None, output=None):
        self.target = target
        self.description = description

        self.deduction = deduction

        # optional components
        self.arguments = arguments      # what arguments to pass (dict)
        self.input = input              # what input to send
        self.value = value              # expected return value
        self.output = output            # expected output


    def __str__(self):
        return "eval of {} ({} pts.)".format(self.target,
                                             self.deduction)


    def to_dict(self):
        test_dict = {'type': self.json_type,
                     'description': self.description,
                     'deduction': self.deduction,
                     'arguments': self.arguments,
                     'input': self.input,
                     'value': self.value,
                     'output': self.output}

        return test_dict


    @staticmethod
    def from_dict(dict_obj):
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
        else:
            raise ValueError("invalid target type")


    def __run_function(self, context):
        import sys
        import io

        mod_name = context.__name__
        fn_name = self.target.name

        if self.arguments:
            if type(self.arguments) is dict:
                args = ["{}={}".format(k, v) for (k, v) in self.arguments.items()]
            else:
                args = self.arguments

            formatted_args = ', '.join(args)
        else:
            formatted_args = ""

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
            passed = passed and self.output == output

        if passed:
            return None
        else:
            result =  {'deduction': self.deduction,
                       'description': self.description,
                       'notes': []}

            if self.value is not None:
                result['notes'].append("expected value: " + str(self.value))
                result['notes'].append("produced value: " + str(return_value))

            if self.output is not None:
                import util
                eo, po = util.escape(self.output), util.escape(output)

                result['notes'].append("expected output: " + eo)
                result['notes'].append("produced output: " + po)

            return result


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



class ReviewTest(BaseTest):
    json_type = 'review'

    def __init__(self, target, description, deduction):
        super().__init__(description, deduction)

        # target can be a PythonFile or PythonFunction
        self.target = target


    def __str__(self):
        return "review of {} ({} pts.)".format(self.target,
                                               self.deduction)


    def to_dict(self):
        test_dict = {'type': self.json_type,
                     'description': self.description,
                     'deduction': self.deduction}

        return test_dict


    @staticmethod
    def from_dict(dict_obj):
        args = {'target': None,
                'description': dict_obj['description'],
                'deduction': dict_obj['deduction']}

        return ReviewTest(**args)


    def run(self, context):
        """Perform a 'review' test by acquring the source code of the function
        or module and printing it. The context is not used. A human is asked
        to confirm the deduction.
        """
        if type(self.target) is PythonFile:
            src = open(self.target.path).read()

        elif type(self.target) is PythonFunction:
            import inspect

            for m in inspect.getmembers(context, inspect.isfunction):
                if m[0] == self.target.name:
                    func_obj = m[1]
                    break
            else:
                return {'deduction': self.deduction,
                        'description': self.description,
                        'notes': ["could not find {}".format(self.target)]}

            src = inspect.getsource(func_obj)

        print(src)
        print("deduction description: {}".format(self.description))
        print("deduction value: {}".format(self.deduction))

        while True:
            ans = input("Should this deduction be taken (y/n)? ")

            if ans in ['y', 'n', 'yes', 'no']:
                break

        if ans == 'y' or ans == 'yes':
            # the deduction *should* be taken, therefore this test fails
            return {'deduction': self.deduction,
                    'description': self.description,
                    'notes': ["failed human review"]}
        else:
            # the deduction *should not* be taken, therefore this test passes
            return None



class PythonFile(PlainFile):
    json_type = 'python'
    extensions = ['py']
    supported_tests = PlainFile.supported_tests.copy()
    supported_tests.append(ReviewTest)
    supported_tests.append(EvalTest)


    def __init__(self, path, tests=None, functions=None, variables=None):
        self.path = path
        self.tests = tests if tests else []
        self.functions = functions if functions else []
        self.variables = variables if variables else []
        self.point_value = sum([f.point_value for f in self.functions])


    @staticmethod
    def from_dict(dict_obj):
        args = {'path': dict_obj['path'],
                'tests': [],
                'functions': [],
                'variables': []}

        if 'tests' in dict_obj:
            for t in dict_obj['tests']:
                test_cls = filetypes.find_test_class(t['type'])
                if test_cls not in cls.supported_tests:
                    raise ValueError("file type '{}' does not support"
                                     "test type '{}'".format(cls.json_type,
                                     t['type']))

                args['tests'].append(test_cls.from_dict(t))

        for f in dict_obj['functions']:
            args['functions'].append(PythonFunction.from_dict(f))

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


    # note: this function replaces the function from PlainFile and runs two
    # categories of tests: module-level tests (which are in self.tests) and
    # function-level tests (which are in f.tests for each f in self.functions)
    def run_tests(self):
        results = dict()
        results[self] = []

        try:
            module_context = self.__import_module()
        except ImportError as err:
            return [{'deduction': self.point_value,
                     'description': "importing '{}'".format(self.path)}]

        found_functions = self.__get_members(module_context, 'functions')
        found_variables = self.__get_members(module_context, 'variables')

        for test in self.tests:
            result = test.run(module_context)
            if result is not None:
                results[self].append(result)

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
                    results[func].append(result)

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
                    results[var].append(result)

        for target, failures in results.items():
            sum = 0
            for f in failures:
                sum += f['deduction']

                if sum > target.point_value:
                    f['deduction'] = 0

        return [item for subl in results.values() for item in subl]


    def __import_module(self):
        import os
        import sys

        directory, name = os.path.split(self.path)
        mod_name = name[:name.index('.py')] if '.py' in name else name

        if directory not in sys.path:
            sys.path.append(directory)

        return __import__(mod_name)


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
                test_cls = filetypes.find_test_class(t['type'])
                args['tests'].append(test_cls.from_dict(t))

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
                test_cls = filetypes.find_test_class(t['type'])
                args['tests'].append(test_cls.from_dict(t))

        # set target of tests for module to this new PythonVariable object
        new = PythonVariable(**args)
        for test in new.tests:
            test.target = new

        return new


    def to_dict(self):
        return {'variable_name': self.name,
                'point_value': self.point_value,
                'tests': [t.to_dict() for t in self.tests]}
