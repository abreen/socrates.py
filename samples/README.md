These sample files can be used to test `socrates` in generate and grading
modes. To generate a skeleton criteria file from the "Problem Set 0"
solution module, try

    python ../socrates.py gen solution/ps0.py

which should create a file `ps0.criteria.json` in the current directory,
containing a criteria file that requires the presence of the `ps0` module
as well as all functions declared in that module. The point value of the
module as well as all functions are initialized to 0, and no tests are
included.

After generating this criteria, arbitrary tests can be added to the
criteria file and the sample student submission can be checked against those
tests with

    python ../socrates.py grade ps0.criteria.json submission/ps0.py

which will start an interactive grading session, at the end of which a
grade file `ps0.grade.txt` will be created which contains a list of
point values, any failed tests and associated deductions, and point
total.

The grading session won't feel very "interactive" if there weren't any tests
specified that require human input (e.g., a test with the `review` action).
`socrates` will auto-grade using the tests with actions like `eval`,
`output`, etc. by evaluating expressions and calling functions when necessary.
If `socrates` encounters a stack overflow while evaluating a recursive
function, it will quitely declare the test failed and continue auto-grading.
If it encounters very long-running code (over 15 seconds of real-world time)
it will prompt the grader to interrupt the test by sending `SIGINT`. If the
user sends `SIGINT`, `socrates` will declare the test failed.
