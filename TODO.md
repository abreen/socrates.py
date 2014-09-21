* Refactor test set code
* Having from_json() in addition to constructors is confusing
* Add mode where all possible deductions are listed
* Add other test types specific to files:
    - "picobot" with the usual default attributes as well as an attribute
      "maps", a list of file paths to map files that will be used to test the
      student's Picobot rules
    - "logisim" with the usual default attributes as well as a "truth_tables"
      attribute that takes a file path to a special file with the expected
      truth tables of circuits part of a student's submission
