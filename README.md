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

The grader uses `socrates` in *grade* mode, in which the criteria file is
specified and one or more submission files are specified. `socrates` will
read the criteria file to obtain a list of expected modules and functions,
and for each module in the submission, run any tests specified in the
criteria file. When `socrates` finds a failed test, it will deduct the
appropriate amount from the student's score. `socrates` also has a special
"review" test, which will cause the auto-grading to pause while a human
reviews the submission and applies manual deductions, if necessary.

When `socrates` exits in *grade* mode, a final grade file is written,
containing any failed tests and the deductions associated with the tests,
along with the total score. If a module or function is missing, `socrates`
will deduct the value of the module or function and skip any tests written
for the module or function.


Criteria files
--------------

A criteria file is a plain text file containing one JSON object with three
attributes: the name of the problem set, the total number of non-extra credit
points, and an array of module objects.

    {
      "assignment_name": <assignment_name>,
      "point_total": <total>,
      "modules": [ module_0, ..., module_n ]
    }


Each module object specifies the required components of the Python module,
including any variable or function definitions, and any imports the Python
module should make. A point value is associated with the existence of each.
A module object also contains zero or more *tests* that
`socrates` will use in grading mode. *Note:* If `socrates` is given a criteria
file containing more modules than are provided as part of a submission, it
will deduct the sum of the point values of each required function, variable,
or import.

    {
      "module_name": <module_name>,
      "required_functions": [ function_0, ..., function_n ],
      "required_variables": [ var_0, ..., var_m ],
      "required_imports": [ module_0, ..., module_p ],
      "tests": [ test_0, ..., test_q ]
    }

In grading mode, `socrates` will use the `required_functions`,
`required_variables`, and `required_imports` arrays to check the student
submission. Let's look at the structure of a sample function object:

    {
        "function_name": "fibonacci",
        "formal_parameters": [ "n" ],
        "point_value": 5
    }

Here's a sample variable object:

    {
        "variable_name": "my_var",
        "point_value": 1
    }

And here's a sample import object:

    {
        "import_name": "functools",
        "point_value": 3
    }

If any of these functions, variables or imports are found to be missing by
`socrates`, their point values will be subtracted from the student's score,
and the tests for those items will be skipped.

Let's take a look at a sample test object (arrays of these are kept in the
module object in the criteria file):

    {
        "type": "eval",
        "target": "function",
        "name": "fibonacci",

        "arguments": { "n": 0 },
        "expected": 0,

        "deduction": 2,
        "description": "Fibonacci base case"
    }

This test causes `socrates` to evaluate `fibonacci(n=0)` as part of the test.
If the function does not return the specified value of zero, a two-point
deduction is taken with the reasoning `"failed test: Fibonacci base case"`.

Any number of tests can be specified for a certain function, variable or
import. If an item fails many tests, no more than the value of the entire
item will be deducted from the student's score.


