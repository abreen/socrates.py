* Refactor test set code
* Add pre- and post-test batch hooks
* Could PythonFile pre-test batch hook be importing module?
* PythonFile needs to not take more deductions than the value of the function
* Add batch grading mode
* Add optional 'socrates_dir' to criteria file; a directory where solution keys
  and other files can be stored so tests may refer to files outside of a
  student submission directory
* Add other test types specific to files:
    - "picobot" with the usual default attributes as well as an attribute
      "maps", a list of file paths to map files that will be used to test the
      student's Picobot rules
    - "logisim" with the usual default attributes as well as a "truth_tables"
      attribute that takes a file path to a special file with the expected
      truth tables of circuits part of a student's submission
