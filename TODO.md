* Add test sets (use README.md for specification)
    - change test set to have a 'type' of set
    - add test set class
* Add --quiet mode
* Add batch grading mode
* Add diffs to failed tests (for value and output)
  For example: -10  failed test: simple test
                    expected output: Hello, world!\n
                    produced output: Hello, world!
* Add optional 'socrates_dir' to criteria file; a directory where solution keys
  and other files can be stored so tests may refer to files outside of a
  student's submission directory
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
