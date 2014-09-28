socrates
========

![The man himself](https://raw.githubusercontent.com/abreen/socrates/master/socrates.jpg)

`socrates` is a grading application designed for automation of grading tasks,
like running tests on Python modules and other plain text files.  Its primary
functions are generating grading criteria files from an existing solution (the
*generate* mode) and providing an interactive grading session for graders (the
*grade* mode).

Generate mode allows instructors to create a basic starting point for
their criteria files, which are required to actually start grading student
submissions. A solution to a given assignment can be specified, and a
bare `.criteria.json` file will be produced, to which point values, tests,
and other features can be added. Then the `.criteria.json` file can be
sent along to the grader.

The grader uses `socrates` in grade mode, in which the criteria file is
specified and zero or more submission files are specified. `socrates` will
read the criteria file to obtain a list of expected files, and, for each
expected file, run any tests specified in the criteria. When a submission fails
a test, `socrates` deducts the appropriate amount from the student's score.
`socrates` also has a special "review" test, which will cause the auto-grading
to pause while a human reviews the submission and applies manual deductions, if
necessary.

When `socrates` exits in grade mode, a final grade file is written,
containing any failed tests and the deductions associated with the tests,
along with the total score. If an expected component is missing, `socrates`
will deduct the value of the component and skip any tests written for it.


Criteria files
--------------

**Warning:** this documentation about criteria files is very outdated.
It will be brought up to date soon.

A criteria file is a plain text file containing one JSON object with four
attributes: the name of the problem set, the file name-safe name, the
name of the course (used when writing the final grade file), and an array of
file objects.

    {
      "assignment_name": <assignment_name>,
      "short_name": <short_name>,
      "course_name": <course_name>,
      "files": [ file_0, ..., file_n ]
    }

Zero or more file objects can be specified. All file objects must have the
following basic structure (square brackets indicate optional attributes,
parentheses indicate a choice, items inside angle brackets should be replaced
with literals of your choosing):

    {
        "path": <file_path>,
        "type": ("plain" | "python"),
        "point_value": <value>,
        ["tests": [ test_0, ..., test_n ]]
    }

Note that, in the case of a relative path, `socrates` will use its current
working directory as the root.

A file object can have zero or more tests. A file's `type` attribute
determines which tests can be used to test that file. For example, a file of
type `plain` can be tested using the `diff` test, which (as it sounds)
causes `socrates` to run a diff against a solution file. Or, for a file of
type `python`, more complex tests can be run on the file.


Testing Python module submissions
---------------------------------

Since `socrates` was written in Python and intended to grade assignments
written in Python, it has specific Python module-testing abilities. To use
these features, specify `python` as the file type for a Python file you
intend to test. When you use the `python` file type, you can list the functions
you expect to be in the student's submission in the `functions` array, along
with any tests designed for those functions. Here's an example file object with
the `python` file type:

    {
        "path": "ps0.py",
        "type": "python",
        "functions": [
            {
                "function_name": "fibonacci",
                "parameters": [ "n" ],
                "point_value": 5,
                "tests": [
                    { "type": "eval",
                      "arguments": { "n": 0 },
                      "value": 0,
                      "deduction": 2,
                      "description": "Fibonacci base case of F_0"
                    },
                    { "type": "eval",
                      "arguments": { "n": 1 },
                      "value": 1,
                      "deduction": 2,
                      "description": "Fibonacci base case of F_1"
                    }
                ]
            }
        ]
    }


Note that this example file object does not contain a `tests` attribute, which
means that `socrates` will not perform any module-level tests. However, the
`fibonacci` function has two tests written for it.

As part of each test, `socrates` will evaluate `fibonacci(n=0)` and
`fibonacci(n=1)`. If the `fibonacci(n=0)` does not return the expected value of
0, a two-point deduction is taken.

If the `fibonacci` function were missing from a student submission, its total
point value would be subtracted from the student's score, and both of these
tests for it would be skipped.

If a function (or module) fails many tests, no more than the value of the
entire item will be deducted from the student's score.

Note also that this file object does not have a `point_value` attribute,
although it was listed as required in the previous section! For `python` file
types, `socrates` will use the sum of the values of all functions as the total
value for the module.


### Tests for Python functions

Each test has an associated *type*. The two tests above were `eval`
tests, which will cause `socrates` to call `eval()` on the function, with
the given arguments and/or simulated human input on the keyboard. Either
the return value of the function or the output of the function (or both)
can be checked against expected values. If the function fails to
run, causes a stack overflow, runs too long, or produces an incorrect
value, `socrates` will fail the test.

`review` tests simply cause `socrates` to pause auto-grading and
present the human grader with the source code of the target module or
function. The human will be presented with the test's deduction and
description, and decide whether the deduction is applied.

Here's the specification of a JSON test object, which can be located in a
module object's or function object's `tests` array (square brackets indicate
optional attributes, parentheses indicate a choice, items inside angle
brackets should be replaced with literals of your choosing):

    {
        "type": ("eval" | "review"),
        "description": <string>,
        "deduction": <integer>,
        ["arguments": { <arg-name>: <arg-value>, ... },]
        ["input": <string>,]
        ["value": <string>,]
        ["output": <string>]
    }

Any or all of the attributes `arguments`, `input`, `value`, and `output`
can be specified (and in any order); if present, they will cause `socrates`
to behave according to the following specifications:

* when `arguments` is specified, `socrates` will call the specified function
  with the given arguments (here, `null` as a replacement for `<arg-value>`
  is allowed and will correspond to Python's `None`);
* when `input` is specified, `socrates` will run the function and supply the
  input string as if it were entered by a human on the keyboard;
* when `value` is specified, `socrates` will compare the return value of the
  function (here, `null` is allowed and will correspond to Python's `None`);
* when `output` is specified, `socrates` will capture any bytes sent to the
  standard out while the function is run and compare it to the specified value

Note that, if the `arguments` attribute is missing or if it has a value of
`null`, the target function will be called with no arguments.

If either `value` or `output` does not match the expected value, `socrates`
will fail the test.


### Testing variables in a Python module

A file object of type `python` can also specify required variables in the
module. Similarly to functions, specifying variables is done by creating
an array of JSON objects in an attribute `variables` in a Python file
object. For example:

    {
        "type": "python",
        "path": "demo/mymodule.py",
        "variables": [
            {
                "variable_name": "var1",
                "point_value": 10,
                "tests": [
                    {
                        "type": "eval",
                        "description": "var1 should be zero",
                        "deduction": 8,
                        "value": 0
                    }
                ]
            }
        ]

Python variables can include `eval` and `review` tests. For `eval` tests,
only the `value` attribute can be specified. `socrates` will simply evaluate
the variable and take the deduction if it does not evaluate to `value`.


Test sets
---------

A *test set* object is a special test type that contains
one or more member test objects. A test set allows `socrates` to deduct
specific point values based on how many tests in the set fail. For example,
it may be desired to perform five tests and deduct 2 points if one
test fails, 3 points if two or three tests fail, and 5 points if four or more
tests fail. The exact deductions can be specified by way of a *deduction map*,
shown below:

    {
        "type": "set",
        "deductions": { "1": 2, "2": 3, "5": 4 },
        "members": [
            ...
        ]
    }

`socrates` uses the lowest attribute in the deduction map as the lower bound
for deductions and the highest attribute in the map as the maximum deduction.
Member tests do not need to specify individual deductions.
For example, for the deduction map

    { "2": 4, "4": 6, "5": 10 }

no points will be deducted if zero or one tests fail. If two or three tests
fail, 4 points are deducted. If four tests fail, 6 points are deducted.
If five or more tests fail, 10 points are deducted.
