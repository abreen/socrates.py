import inspect

from util import *
from criteria import *


class Evaluation:
    """Objects of this class are used in grading mode to tabulate deductions
    given a Criteria object, which specifies the required components of a
    submission, and any submission files from the student. When a final grade
    file is needed, the Evaluation object associated with the submitted files
    is consulted.
    """

    def __init__(self, criteria):
        self.criteria = criteria

        # all Test objects from the specified criteria associated with the
        # imported module object from the student submission (so that the
        # test can be run within the context of a student's submission)
        # dict key: Test object
        # dict value: imported module object
        self.tests = dict()

        # dict keys: Function or Module object
        # dict values: list of failed Tests or None
        # only functions or modules that failed any tests are present
        self.failed_tests = dict()

        # dict keys: Function or Module object
        # dict values: actual imported object or None
        self.submission = dict()

        for module in criteria.modules.values():
            self.submission[module] = None

            for module_test in module.tests:
                self.tests[module_test] = None

            for func in module.functions.values():
                self.submission[func] = None

                for func_test in func.tests:
                    self.tests[func_test] = None


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

        # find tests in this Evaluation that have this module as a target;
        # we will add the imported module so that tests can be run with
        # the student's actual code
        for test in self.tests:
            if type(test.target) is Module and \
               test.target.name == module.__name__:
                self.tests[test] = module

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

                # we also add the function's parent module to any tests
                # for this function, so that tests on this function can be
                # run with the student's code
                for test in self.tests:
                    if type(test.target) is Function and \
                       test.target.name == func_name:
                        self.tests[test] = module


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
                ded = t.deduction
                desc = t.description

                if ded + points_lost > total_value:
                    ded = 0
                else:
                    points_lost += t.deduction

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
