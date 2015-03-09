import sys
import yaml

import filetypes
from filetypes.plainfile import PlainFile, ReviewTest
from filetypes.basefile import TestSet, BaseFile
from filetypes.basetest import BaseTest
from util import sprint, add_to, warn, COLOR_GREEN, \
                 COLOR_RED, COLOR_RESET, ALPHABET, plural

MAX_STACK_SIZE = sys.getrecursionlimit()
BASIC_TYPES = [str, int, float, bool, list, dict, type(None)]


class CriteriaObject:
    """An object type specified by the criteria is represented using an
    instance of this class. When the student's module is loaded, this
    object is "converted" to an instance of a class from the student
    submission.
    """
    def __init__(self, class_name, attrs):
        self.class_name = class_name
        self.attrs = attrs


def crit_obj_constructor(loader, suffix, node):
    class_name = suffix.split(':')[-1]
    attrs = loader.construct_mapping(node)
    return CriteriaObject(class_name=class_name, attrs=attrs)

yaml.add_multi_constructor(u'!object', crit_obj_constructor)


class EvalTest(BaseTest):
    yaml_type = 'eval'

    def __init__(self, dict_, file_type):
        super().__init__(dict_, file_type)

        # note: self.description might be None if no description was
        # specified in the YAML file; this is okay, since we can construct
        # a default one after self.target is set

        # target could be a PythonFunction, PythonVariable or PythonMethod
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
                raise ValueError("specifying arguments positionally is no "
                                 "longer allowed; specify them as a dict")

            elif type(dict_['arguments']) is dict:
                for param_name, param_val in dict_['arguments'].items():
                    self.arguments.append((param_name, param_val))
            else:
                raise ValueError("arguments to this eval test must "
                                 "be specified")

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

        # need prestate and poststate attributes if we are testing a
        # method so that we can check how a method might affect the
        # called object
        self.before = None
        if 'before' in dict_:
            self.before = dict_['before']

        self.after = None
        if 'after' in dict_:
            self.after = dict_['after']

        # if 'prompt' is specified and is True, the eval test will not fail
        # unless a human confirms the failure
        self.prompt = None
        if 'prompt' in dict_:
            self.prompt = dict_['prompt']


    def __str__(self):
        return "eval of {} ({} pts.)".format(self.target,
                                             self.deduction)


    def run(self, cxt):
        sprint("running eval test on {}... ".format(self.target), end='')

        result = None
        if type(self.target) in [PythonFunction, PythonMethod]:
            result = self.__run_function(cxt)
        elif type(self.target) is PythonVariable:
            result = self.__run_variable(cxt)
        elif type(self.target) is PythonFile:
            result = self.__run_module(cxt)
        else:
            raise ValueError("invalid target type")

        if result:
            sprint("failed", color=COLOR_RED)
        else:
            sprint("passed", color=COLOR_GREEN)

        return result


    def __run_function(self, context):
        import sys
        import io
        import random

        mod_name = context.__name__
        fn_name = self.target.name
        testing_method = type(self.target) is PythonMethod

        before = self.before

        if before and type(before) is CriteriaObject:
            before = _convert_using_cxt(context, before)

        args = self.__get_args(mod_name, context)

        if type(args) is tuple:
            return {'deduction': self.deduction,
                    'description': self.description,
                    'notes': ["cannot test function",
                              "unexpected number of parameters "
                              "(expected {}, submission has {})".format(
                              args[0], args[1])]}

        locals = {mod_name: context}
        vars = ALPHABET[:len(args)]
        args_strings = []

        for i in range(len(vars)):
            locals[vars[i]] = args[i][1]
            args_strings.append("{}={}".format(args[i][0], vars[i]))

        fn_call = "{}({})".format(fn_name, ', '.join(args_strings))

        if testing_method:
            locals["obj"] = before
            code = "obj." + fn_call
        else:
            code = mod_name + "." + fn_call

        if not self.description:
            self.description = self.__build_description()

        # redirect standard in to buffer
        if self.input is not None:
            in_buf = io.StringIO(self.input)
        else:
            in_buf = io.StringIO()

        sys.stdin = in_buf

        # redirect standard out to buffer
        out_buf = io.StringIO()
        sys.stdout = out_buf

        if self.random_seed:
            random.seed(self.random_seed)

        try:
            return_value = eval(code, globals(), locals)
        except KeyboardInterrupt:
            sys.stdin, sys.stdout = sys.__stdin__, sys.__stdout__

            sprint(COLOR_RED + "interrupting a test" + COLOR_RESET)

            return {'deduction': self.deduction,
                    'description': self.description,
                    'notes': ["test was interrupted by the grader"]}
        except:
            import sys
            err = sys.exc_info()

            sys.stdin, sys.stdout = sys.__stdin__, sys.__stdout__

            warn("failing a test due to an error ({})".format(err[1]))

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

        # if we are testing a method and there are post-state requirements
        # for the method, fail the test if the object doesn't match the
        # required post-state
        if testing_method and self.after is not None:
            if not _attributes_equal(locals["obj"], self.after):
                passed = False

        if passed:
            return None
        else:
            result = {'deduction': self.deduction,
                      'description': self.description,
                      'notes': []}

            if self.arguments:
                for arg, val in self.arguments:
                    s = "where '{}' is {}".format(arg, _safe_str(val))
                    result['notes'].append(s)

            if testing_method and before is not None:
                result['notes'].append("called object before "
                                       "the method call: "
                                       "{}".format(_safe_str(before)))

            if self.value is not None:
                result['notes'].append("expected value: " + \
                                       _safe_str(self.value))
                result['notes'].append("produced value: " + \
                                       _safe_str(return_value))

            if self.output is not None and type(self.output) is str:
                import util
                eo, po = util.escape(self.output), util.escape(output)

                result['notes'].append("expected output: " + eo)
                result['notes'].append("produced output: " + po)

            if testing_method and self.after is not None:
                result['notes'].append("expected object after "
                                       "the method runs: "
                                       "{}".format(_safe_str(self.after)))

            if self.prompt:
                if self.__should_fail(result):
                    return result
                else:
                    return None
            else:
                return result


    def __should_fail(self, result):
        """Called before an eval test is about to be failed, but the criteria
        specifies that a human should confirm the failure before taking
        any points. If this method returns True, the points are ultimately
        taken.
        """
        import sys
        from grader import write_results
        from prompt import prompt

        warn("about to fail a test with the following reasoning:")

        write_results(sys.stdout, [result])

        points = result['deduction']
        s = plural("point", points)
        fail_msg = "fail this test (-{} {})".format(points, s)

        choices = [fail_msg, "do not fail this test"]
        return prompt(choices, '1') == [0]


    def __build_description(self):
        """Builds a description automatically from the target of this eval
        test, using the arguments to the function or method (if applicable),
        any expected output on given input, return values, and object state
        before and after (if applicable).
        """
        s = ""

        if self.random_seed is not None:
            s += "on random seed {}, ".format(self.random_seed)

        if self.input is not None:
            s += "with input {}, ".format(repr(self.input))

        if self.before is not None:
            s += "on the called object: {}, ".format(_safe_str(self.before))

        s += str(self.target)    # e.g. "function test(a, b)"
        s += " should "

        if self.output is not None:
            s += "output {}".format(repr(self.output))

        if self.value is not None:
            if self.output is not None:
                s += " and "

            s += "return {}".format(_safe_str(self.value))

        if self.after is not None:
            s += ", ending with {}".format(_safe_str(self.after))

        if self.output is not None and \
           self.value is not None and \
           self.after is not None:
            s += "should work correctly"

        return s


    def __get_arg_value(self, param_name):
        """Given the name of a parameter to a function or method, find the
        value of the actual argument to that parameter as specified by this
        eval test, or None if there is no such parameter.
        """
        for arg_name, val in self.arguments:
            if arg_name == param_name:
                return val

        return None


    def __get_args(self, mod_name, cxt):
        """Given a particular module context (the student's submitted
        module, after being imported), construct and return a list of
        tuples (n, m) such that all n are the parameter names used by
        the student and all m are the values for those parameters
        (i.e., arguments) specified by this eval test in the criteria
        file. Importantly, this function "converts" CriteriaObject objects
        that were created at the time the YAML file was loaded into actual
        instances of the desired class. (This has to happen here, as opposed
        to when the YAML file is loaded, since the student's module is now
        imported.) If the function or method in the context has the incorrect
        number of parameters, a tuple (a, b) is returned, where a is the
        expected number of parameters and b is the student's number of
        parameters. For methods, this function does not return a tuple
        containing "self".
        """
        if not self.arguments:
            return []

        from inspect import signature

        func_obj = _find_function_from_cxt(cxt, self.target)
        student_param_names = list(signature(func_obj).parameters)

        # for methods, we should remove "self" from the
        # parameter list
        if type(self.target) is PythonMethod:
            del student_param_names[0]

        args = []

        # if the number of parameters in the criteria file does not
        # match the number of the student's submission, we return
        # an error tuple
        if len(self.target.parameters) != len(student_param_names):
            t = (len(self.target.parameters), len(student_param_names))
            return t

        for i in range(len(self.target.parameters)):
            param_name = self.target.parameters[i]
            arg_val = self.__get_arg_value(param_name)

            if type(arg_val) is CriteriaObject:
                arg_val = _convert_using_cxt(cxt, arg_val)

            args.append((student_param_names[i], arg_val))

        return args


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


class PythonReviewTest(ReviewTest):
    def __init__(self, dict_, file_type):
        super().__init__(dict_, file_type)

        # TODO get rid of this
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

        elif type(self.target) in [PythonFunction, PythonMethod]:
            import inspect
            func_obj = _find_function_from_cxt(context, self.target)

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
        BaseFile.__init__(self, dict_)

        self.functions = []
        self.classes = []
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

        if 'classes' in dict_:
            for c in dict_['classes']:
                self.classes.append(PythonClass(c))

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
            if new_val > MAX_STACK_SIZE:
                sprint("code wants to set stack size too large")
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

            warn("deducting {} points for import error".format(deduction))

            return [{'deduction': deduction,
                     'description': "error importing '{}'".format(self.path),
                     'notes': ["encountered {}".format(err[0].__name__)]}]

        found_functions = self.__get_members(module_context, 'functions')
        found_classes = self.__get_members(module_context, 'classes')
        found_variables = self.__get_members(module_context, 'variables')

        for test in self.tests:
            result = test.run(module_context)
            if result is not None:
                add_to(result, results[self])

        for func in self.functions:
            results[func] = []
            if func not in found_functions:
                results[func].append({'deduction': func.point_value,
                                      'description': "missing "
                                                     "{}".format(func)})
                continue

            for test in func.tests:
                # TODO fix this hacky thing
                if type(test) is TestSet:
                    for m in test.members:
                        m.target = func

                result = test.run(module_context)
                if result is not None:
                    add_to(result, results[func])

        for cls in self.classes:
            results[cls] = []
            if cls not in found_classes:
                results[cls].append({'deduction': cls.point_value,
                                     'description': "missing "
                                                    "{}".format(cls)})
                continue

            # TODO move this into __get_members
            cls_obj = _find_class_from_cxt(module_context, cls.name)
            import inspect

            found_methods = []
            for m in inspect.getmembers(cls_obj, inspect.isfunction):
                for method in cls.methods:
                    if method.name == m[0]:
                        found_methods.append(method)


            for method in cls.methods:
                results[method] = []

                if method not in found_methods:
                    results[method].append({'deduction': method.point_value,
                                            'description': "missing "
                                                        "{}".format(method)})
                    continue

                for test in method.tests:
                    # TODO fix this hacky thing
                    if type(test) is TestSet:
                        for m in test.members:
                            m.target = method

                    result = test.run(module_context)
                    if result is not None:
                        add_to(result, results[method])

        for var in self.variables:
            results[var] = []
            if var not in found_variables:
                results[var].append({'deduction': var.point_value,
                                     'description': "missing "
                                                    "{}".format(var)})
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
                if 'deduction' in f:
                    # deduction is at top level
                    sum += f['deduction']

                    if sum > target.point_value:
                        f['deduction'] = 0

                elif 'subresults' in f:
                    # deduction for this failure is made up of subresults
                    for subfailure in f['subresults']:
                        sum += subfailure['deduction']

                        if sum > target.point_value:
                            subfailure['deduction'] = 0

        return [item for subl in results.values() for item in subl]



    def __get_members(self, cxt, kind):
        import inspect
        members = []

        if kind == 'functions':
            for m in inspect.getmembers(cxt, inspect.isfunction):
                for f in self.functions:
                    if f.name == m[0]:
                        members.append(f)

        if kind == 'classes':
            for m in inspect.getmembers(cxt, inspect.isclass):
                for c in self.classes:
                    if c.name == m[0]:
                        members.append(c)

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


def _find_function_from_cxt(context, target):
    """This function inspects the passed-in context for a function
    or a method using the passed-in target, either a PythonFunction
    or a PythonMethod.
    """
    from inspect import getmembers, isfunction, ismethod, isclass

    name = target.name

    if type(target) is PythonFunction:
        for m in getmembers(context, isfunction):
            if m[0] == name:
                return m[1]

    if type(target) is PythonMethod:
        cls_name = target.class_name

        for c in getmembers(context, isclass):
            if c[0] == cls_name:
                break
        else:
            raise ValueError("cannot find class {}".format(cls_name))

        for m in getmembers(c[1], isfunction):
            if m[0] == name:
                return m[1]

    return None


def _find_class_from_cxt(context, name):
    """This function inspects the passed-in context for a class
    object that matches the specified class name.
    """
    from inspect import getmembers, isclass

    for c in getmembers(context, isclass):
        if c[0] == name:
            return c[1]

    return None


def _convert_using_cxt(cxt, crit_obj):
    """Given a module context (resulting from importing a student's
    code) and an instance of CriteriaObject, return an object instance
    using the student's class definition, filling the object with the
    attributes found in the CriteriaObject object.
    """
    cls = _find_class_from_cxt(cxt, crit_obj.class_name)
    obj = cls.__new__(cls)

    for attr, val in crit_obj.attrs.items():
        setattr(obj, attr, val)

    return obj


def _attributes_equal(target, expected):
    """Given a "target" object of any type (e.g., the object left over after
    a student's method was called on it), consult the CriteriaObject
    specified second for its attributes, and return True if the target
    object has all the attributes expected and the values of the attributes
    match. Otherwise, return False.
    """
    for attr, val in expected.attrs.items():
        if not hasattr(target, attr) or getattr(target, attr) != val:
            return False

    return True


def _safe_str(obj):
    """Given any object, return a "safe" string representation of the object
    if calling its __str__() method might be considered unsafe. If the object
    is considered a "basic" type (e.g., an integer or a string), the object's
    repr() is used. If the object is a CriteriaObject, the output string is
    indistinguishable from its "converted" form (i.e., "CriteriaObject" will
    be replaced by the underlying class). For non-basic object types, function
    attributes (e.g., methods) are not included in the list of attributes.
    """
    if type(obj) in BASIC_TYPES:
        if type(obj) is bool:
            return repr(obj) + " (a Boolean)"
        else:
            return repr(obj)

    attrs = []

    if type(obj) is CriteriaObject:
        s = obj.class_name + " {"
        for attr, val in obj.attrs.items():
            attrs.append("{}: {}".format(attr, _safe_str(val)))
    else:
        from inspect import isfunction, ismethod

        s = type(obj).__name__ + " {"
        for attr in dir(obj):
            if attr[0] == '_':
                continue
            val = getattr(obj, attr)

            if isfunction(val) or ismethod(val):
                continue

            attrs.append("{}: {}".format(attr, _safe_str(val)))

    s += ', '.join(attrs) + "}"
    return s


class PythonClass:
    """Utility class representing a Python class that the criteria specifies
    should be in a module of a student's submission. Used only with files of
    type 'python'.
    """

    def __init__(self, dict_):
        self.name = dict_['class_name']
        self.point_value = dict_['point_value']

        self.methods = []
        for m in dict_['methods']:
            obj = PythonMethod(m)
            obj.class_name = self.name
            self.methods.append(obj)

        # note: class-level tests not yet supported


    def __str__(self):
        return self.name


class PythonMethod:
    """Utility class representing a Python method that the criteria specifies
    should be in a module of a student's submission. Used only with files of
    type 'python'.
    """
    def __init__(self, dict_):
        self.name = dict_['method_name']

        # note: not counting "self"!
        self.parameters = dict_['parameters']
        self.point_value = dict_['point_value']

        self.tests = []
        if 'tests' in dict_:
            for t in dict_['tests']:
                test_cls = filetypes.find_test_class(PythonFile.yaml_type,
                                                     t['type'])
                self.tests.append(test_cls(t, PythonFile.yaml_type))

        # set target of tests for module to this new PythonMethod object
        for test in self.tests:
            test.target = self


    def __str__(self):
        if self.parameters:
            params = ', '.join(["self"] + self.parameters)
        else:
            params = "self"

        name = "{}({})".format(self.name, params)
        return "method {}".format(name)
