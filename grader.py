import sys
import os

from util import *
from evaluation import *
import files


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

        # run the test, passing in the actual target (function or module
        # object resulting from import) and module context (object returned
        # by __import__())
        actual_target = ev.submission[test.target]
        module_context = ev.tests[test]

        passed = test.run_test(actual_target, module_context)

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


if __name__ == '__main__':
    print("To start a grading session, run the 'socrates' module.")
