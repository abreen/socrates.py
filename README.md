socrates
========

![The man himself](https://raw.githubusercontent.com/abreen/socrates/master/socrates.jpg)

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
        "point_value": 5,
        "tests": [
            { "action": "eval",
              "arguments": { "n": 0 },
              "value": 0,
              "deduction": 2,
              "description": "Fibonacci base case of F_0"
            },
            { "action": "eval",
              "arguments": { "n": 1 },
              "value": 1,
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


### Tests

Each test has an associated *action*. The two tests above were `eval`
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
        "action": ("eval" | "review"),
        "description": <string>,
        "deduction": <integer>,
        ["arguments": { <arg-name>: <arg-value>, ... },]
        ["input": <string>,]
        ["value": <string>,]
        ["output": <string>,]
    }

Any or all of the attributes `arguments`, `input`, `value`, and `output`
can be specified; if present, they will cause `socrates` to behave according
to the following specifications:

* when `arguments` is specified, `socrates` will call the specified function
  with the given arguments (here, `null` as a replacement for `<arg-value>`
  is allowed and will correspond to Python's `None`);
* when `input` is specified, `socrates` will run the function and supply the
  input string as if it were entered by a human on the keyboard;
* when `value` is specified, `socrates` will compare the return value of the
  function (here, `null` is allowed and will correspond to Python's `None`);
* when `output` is specified, `socrates` will capture any bytes sent to the
  standard out while the function is run and compare it to the specified value

If either `value` or `output` does not match the expected value, `socrates`
will fail the test.

### Test sets

In place of a test object, a *test set* object can be specified that contains
one or more member test objects. A test set allows `socrates` to deduct
specific point values based on how many tests in the set fail. For example,
it may be desired to perform five tests and deduct 2 points if one
test fails, 3 points if two or three tests fail, and 5 points if four or more
tests fail. The exact deductions can be specified by way of a *deduction map*,
shown below:

    {
        "deduction_map": { "1": 2, "2": 3, "5": 4 },
        "members": [
            ...
        ]
    }

`socrates` uses the lowest attribute in the deduction map as the lower bound
for deductions and the highest attribute in the map as the maximum deduction.
For example, for the deduction map

    { "2": 4, "4": 6, "5": 10 }

no points will be deducted if zero or one tests fail. If two or three tests
fail, 4 points are deducted. If four tests fail, 6 points are deducted.
If five or more tests fail, 10 points are deducted.
