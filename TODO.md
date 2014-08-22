* Test API changes
    - create package 'tests' in this directory
    - split each type of test into specific classes with their own
      'run_test' methods
    - each test class should specify an ID, e.g. 'eval' or 'review';
      the code in the 'files' package will check all available test class
      to see which tests can handle the ID specified in the criteria file
* Add test sets (use README.md for specification)
    - change test set to have a 'type' of set
    - add test set class
* Add diffs to failed tests (for value and output)
  For example: -10  failed test: simple test
                    expected output: Hello, world!\n
                    produced output: Hello, world!
* Add general file capability to the criteria code, so that graders can specify
  non-Python files on the command line and the criteria can keep track of them
* Add other test types specific to files:
    - "diff" with the usual "description" and "deduction" attributes, as well
      as "expected" attribute that specifies a path to a file against which the
      submitted file will be checked
    - "picobot" with the usual default attributes as well as an attribute
      "maps", a list of file paths to map files that will be used to test the
      student's Picobot rules
    - "logisim" with the usual default attributes as well as a "truth_tables"
      attribute that takes a file path to a special file with the expected
      truth tables of circuits part of a student's submission
