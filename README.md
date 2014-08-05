socrates
========

`socrates` is a grading toolkit written in Python, for assignments in Python.
As a standalone script, its main function is to generate grading criteria files
from existing Python files (the *generate* mode) and provide an interactive
grading session for graders (the *grade* mode).

Generate mode allows instructors to create a basic starting point for
their criteria files, which are required to actually start grading student
submissions. A solution to a given assignment can be specified, and a
bare `.criteria.json` file will be produced, to which point values, tests,
and other features can be added. Then the `.criteria.json` file can be
sent along to the grader.

The grader uses `socrates` in grade mode, in which the criteria file is
specified and one or more submission files are specified. `socrates` will
read the criteria file to obtain a list of expected modules and functions,
and for each module in the submission, run any tests specified in the
criteria file. When `socrates` finds a failed test, it will deduct the
appropriate amount from the student's score. `socrates` also has a special
"review" test, which will cause the auto-grading to pause while a human
reviews the submission and applies manual deductions, if necessary.

When `socrates` exits in grade mode, a final grade file is written,
containing any failed tests and the deductions associated with the tests,
along with the total score. If a module or function is missing, `socrates`
will deduct the value of the module or function and skip any tests written
for the module or function.


Criteria files
--------------

A criteria file is a plain text file containing one JSON object with four
attributes: the name of the problem set, the file name-safe name, the
total number of points, and an array of module objects.

    {
      "assignment_name": <assignment_name>,
      "short_name": <short_name>,
      "total_points": <total>,
      "modules": [ module_0, ..., module_n ]
    }


Each module object specifies the required components of the Python module,
including any function definitions the module should make. A point value
is associated with the existence of each.
A module object also contains zero or more *tests* that
`socrates` will use in grading mode.

    {
      "module_name": <module_name>,
      "functions": [ function_0, ..., function_n ],
      "tests": [ test_0, ..., test_q ]
    }

In grading mode, `socrates` will use the `functions` array to check a
student's submission. Let's look at the structure of a sample
function object:

    {
        "function_name": "fibonacci",
        "parameters": [ "n" ],
        "point_value": 5
        "tests": [
            { "action": "eval",
              "arguments": [ { "n": 0 } ],
              "expected": 0,
              "deduction": 2,
              "description": "Fibonacci base case of F_0"
            },
            { "action": "eval",
              "arguments": [ { "n": 1 } ],
              "expected": 1,
              "deduction": 2,
              "description": "Fibonacci base case of F_1"
            }
        ]
    }

`socrates` will evaluate `fibonacci(n=0)` and `fibonacci(n=1)` as part of
each test. If the `fibonacci(n=0)` does not return the expected value of
0, a two-point deduction is taken with the reasoning
`"failed test: Fibonacci base case of F_0"`.

If the `fibonacci` function were to be found missing by
`socrates`, its total point value would be subtracted from the student's
score, and the tests for it would be skipped.

Any number of tests can be specified for a target function or module.
If an item fails many tests, no more than the value of the entire item
will be deducted from the student's score.


### Test actions

Each test has an associated *action*. The two tests above were `eval`
tests, which will cause `socrates` to call `eval()` on the function, with
the specified arguments in a separate thread. If the function fails to
run, causes a stack overflow, runs too long, or produces an incorrect
value, `socrates` will fail the test.

Tests can also have the `output` action, applied to functions or modules
as targets, which will cause `socrates` to run the function or module
and compare the output with an expected output string. As with `eval`
tests, `output` tests will fail if the output does not match or something
goes wrong.

Finally, `review` tests simply cause `socrates` to pause auto-grading and
present the human grader with the source code of the target module or
function. The human can enter a deduction and description, if necessary.
