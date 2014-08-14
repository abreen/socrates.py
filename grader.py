import sys
import os
import inspect
from io import StringIO         # for capturing standard out

from util import *
from criteria import *
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
