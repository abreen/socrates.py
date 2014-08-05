"""Functions that help create an interactive grading session."""

import sys
import os
import copy

from util import *
import files
import criteria
import inspect



class Evaluation:
    """Objects of this class are used in grading mode to tabulate deductions
    given a Criteria object, which specifies the required components of a
    submission, and any submission files from the student. When a final grade
    file is needed, the Evaluation object associated with the submitted files
    is consulted.
    """

    def __init__(self, criteria):
        self.running_total = criteria.total_points

        self.found_modules = []
        self.found_functions = []

        for module in criteria.modules:



def grade(criteria, submissions):
    """Given a Criteria object and a list of paths to student submissions,
    evaluate the submission files against the criteria, prompting a human
    grader when necessary. Then write the final grade to a file.
    """

    for s in submissions:
        if not os.path.isfile(s):
            sprint("specified file '" + s + "' does not exist", error=True)
            sys.exit(1)

    ev = Evaluation(criteria)

    for s in submissions:
        module_name = files.module_name_from_path(s)

        if not criteria.has_module(module_name):
            sprint("skipping non-required module '" + module_name + "'")
            continue
        else:
            sprint("grading required module '" + module_name + "'")

            try:
                module = __import__(module_name)
            except ImportError:
                

            # if import was successful, add it to found list
            found_modules.append(module_name)

            # then run tests for the module
            _test_module(module)


    sprint("finished grading session")
    return


def _test_module(self, module):
    pass


if __name__ == '__main__':
    print("To start a grading session, run the 'socrates' module.")
