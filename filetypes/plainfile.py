from filetypes.basefile import BaseFile
from filetypes.basetest import BaseTest


class DiffTest(BaseTest):
    json_type = 'diff'

    def __init__(self, description, deduction, against):
        super().__init__(description, deduction)

        import os
        if not os.path.isfile(against):
            raise ValueError("solution file for diff ('{}') "
                             "cannot be found".format(against))

        self.against = against


    @staticmethod
    def from_dict(dict_obj):
        return DiffTest(description=dict_obj['description'],
                        deduction=dict_obj['deduction'],
                        against=dict_obj['against'])


    def run(self, submission):
        import filecmp

        if filecmp.cmp(submission, self.against):
            return None
        else:
            return {'deduction': self.deduction,
                    'description': self.description,
                    'notes': ["files do not match"]}



class PlainFile(BaseFile):
    json_type = 'plain'
    extensions = ['txt']
    supported_tests = BaseFile.supported_tests.copy()
    supported_tests.append(DiffTest)


    def run_tests(self):
        return [t.run(self.path) for t in self.tests]


    def __str__(self):
        return self.path + " (plain text file)"
