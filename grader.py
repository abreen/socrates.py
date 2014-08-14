import sys
from io import StringIO
import os
import copy

from util import *
from criteria import *
import files
import inspect


class Evaluation:
    """Objects of this class are used in grading mode to tabulate deductions
    given a Criteria object, which specifies the required components of a
    submission, and any submission files from the student. When a final grade
    file is needed, the Evaluation object associated with the submitted files
    is consulted.
    """

    def __init__(self, criteria):
        self.criteria = criteria

        # all Test objects from the specified criteria
        self.tests = []

        # (<Function or Module object>, [failed Tests]|None)
        self.failed_tests = dict()

        # (<Function or Module object>, <actual imported object>|None)
        self.submission = dict()

        for module in criteria.modules.values():
            self.submission[module] = None

            for module_test in module.tests:
                self.tests.append(module_test)

            for func in module.functions.values():
                self.submission[func] = None

                for func_test in func.tests:
                    self.tests.append(func_test)


    def add_module(self, module):
        """Given an actual imported module, add the module object to the
        this Evaluation object's submission listing, along with any
        functions inside it that may have been specified by the
        assignment's criteria.
        """

        expected_module = None
        for s in self.submission:
            if s.name == module.__name__ and type(s) is Module:
                expected_module = s
                break
        else:
            raise ValueError("this module is not specified by the criteria")

        # should be overwriting None here
        self.submission[expected_module] = module

        # find functions in this module that are specified by the criteria
        for memb in inspect.getmembers(module, inspect.isfunction):
            func_name = memb[0]
            func_obj = memb[1]

            # if the name of this function was listed as required in the
            # Module object's list of functions, we have found a student's
            # implementation of a required function; therefore we add it to
            # this Evaluation object's submission listing
            exp_function = expected_module.functions[func_name]
            if func_name in expected_module.functions:
                self.submission[exp_function] = func_obj


    def __handle_deductions(self, f, target):
        total_value = 0
        if type(target) is Function:
            total_value = target.point_value
        elif type(target) is Module:
            total_value = target.get_total_points()
        else:
            raise ValueError("target is not Function or Module")

        if target in self.failed_tests:
            points_lost = 0

            for t in self.failed_tests[target]:
                points_lost += t.deduction

                ded = t.deduction
                desc = t.description

                if ded + points_lost > total_value:
                    ded = 0

                f.write("-{}\tfailed test: {}\n".format(ded, desc))

                return points_lost
        else:
            return 0


    def to_file(self, filename=None):
        """Write the final evaluation results to a grade file."""

        import datetime

        if not filename:
            filename = self.criteria.short_name + "-grade.txt"

        point_total = self.criteria.get_total_points()

        with open(filename, 'x') as f:
            f.write("Grade Report: {}\n".format(self.criteria.assignment_name))
            f.write("{}\n".format(self.criteria.course_name))

            today = datetime.date.today()
            f.write(today.strftime("%B %d, %Y") + "\n")
            f.write("\n")

            for m in self.criteria.modules.values():
                points = m.get_total_points()
                module_heading = "{}.py ({} points)".format(m.name, points)
                f.write(heading(module_heading, level=1))

                if self.submission[m] == None:
                    value = m.get_total_points()
                    point_total -= value
                    f.write("-{}\tnot submitted\n".format(value))
                    continue

                point_total -= self.__handle_deductions(f, m)

                f.write("\n")

                for func in m.functions.values():
                    f_points = func.point_value
                    func_heading = "{} function ({} points)".format(func.name,
                                                                    f_points)
                    f.write(heading(func_heading, level=2))

                    if self.submission[func] == None:
                        value = func.point_value
                        point_total -= value
                        f.write("-{}\tnot submitted\n\n\n".format(value))
                        continue

                    point_total -= self.__handle_deductions(f, func)

                    f.write("\n\n")


            f.write("Total: {}\n".format(point_total))




def grade(criteria, submissions):
    """Given a Criteria object and a list of paths to student submissions,
    evaluate the submission files against the criteria, prompting a human
    grader when necessary. Then write the final grade to a file.
    """

    for s in submissions:
        if not os.path.isfile(s):
            sprint("'{}' is not a file".format(s), error=True)
            sys.exit(1)

    grade_filename = criteria.short_name + '-grade.txt'

    if os.path.isfile(grade_filename):
        sprint("refusing to overwrite existing grade file", error=True)
        sys.exit(1)

    ev = Evaluation(criteria)

    for s in submissions:
        directory, name = os.path.split(s)
        module_name = name[:name.index('.py')] if '.py' in name else name

        if module_name not in criteria.modules:
            sprint("skipping non-required module '{}'".format(module_name))
            continue
        else:
            sprint("adding required module '{}'".format(module_name))

            if directory not in sys.path:
                sys.path.append(directory)

            try:
                module = __import__(module_name)
                globals()[module_name] = module

            except ImportError:
                sprint("importing '{}' failed".format(module_name), error=True)
            else:
                ev.add_module(module)

    # all modules in submission have been imported
    sprint("running tests")

    for test in ev.tests:
        if ev.submission[test.target] == None:
            sprint("skipping {}; target missing".format(test.target))
            continue

        passed = _run_test(test, ev.submission[test.target])

        if not passed:
            sprint("failed: {}".format(test), color=COLOR_YELLOW)
            if test.target not in ev.failed_tests:
                ev.failed_tests[test.target] = [test]
            else:
                ev.failed_tests[test.target].append(test)
        else:
            sprint("passed: {}".format(test), color=COLOR_GREEN)


    ev.to_file(filename=grade_filename)

    sprint("finished grading session")
    return


# TODO this should really be a Test object method, but when I had it
# in the criteria.py file, it was like the __import__()'d modules here
# were out of scope there; we might be able to pass the module object in
# as well as the test target if this function were a Test method
def _run_test(test, actual_target):
    if type(actual_target) is Module:
        # TODO implement testing for modules
        return True

    mod_name = test.target.parent_module.name
    name = actual_target.__name__
    formatted_args = _format_args(test)
    call = "{}.{}({})".format(mod_name, name, formatted_args)

    if test.action == 'eval':
        try:
            result = eval(call)
        except TypeError:
            sprint("failure: incorrect argument type or name")
            return False
        except:
            sprint("spectacular failure: {}".format(test), error=True)
            return False

        return result == test.expected

    elif test.action == 'output':
        old_stdout = sys.stdout
        output = StringIO()
        sys.stdout = output

        eval(call)

        sys.stdout = old_stdout

        return output.getvalue() == test.expected

def _format_args(test):
    """Return a string that, when placed inside of calling parentheses
    and eval()'d, should call the function with the appropriate arguments.
    """

    args = test.arguments

    if type(args) is dict:
        args = ["{}={}".format(k, v) for (k, v) in args.items()]

    return ', '.join(args)


if __name__ == '__main__':
    print("To start a grading session, run the 'socrates' module.")
