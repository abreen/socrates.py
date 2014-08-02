"""Functions that help create an interactive grading session."""

import criteria
import files


class GradingSession:

    def __init__(self, criteria_file, submissions):
        self.criteria = files.from_json(criteria_file)
        self.submissions = submissions

        # TODO create a hash map of module names to ExpectedModules
        # TODO create a hash map of function names to ExpectedFunctions


    def start(self):
        # for each submission file, skip non-required modules
        # then try to import the module and use inspection to auto-correct
        pass
