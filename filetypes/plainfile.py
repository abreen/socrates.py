from filetypes.basefile import BaseFile
from filetypes.basetest import BaseTest


class ReviewTest(BaseTest):
    json_type = 'review'

    def __init__(self, description, deduction):
        super().__init__(description, deduction)


    def __str__(self):
        return "review of {} ({} pts.)".format(self.target,
                                               self.deduction)


    @staticmethod
    def from_dict(dict_obj, file_type):
        args = {'description': dict_obj['description'],
                'deduction': dict_obj['deduction']}

        return ReviewTest(**args)


    def run(self, path):
        f = open(path, 'rb')

        while True:
            c = f.read(1)
            if not c:
                break
            if c == '\r':
                continue
            if c == '\n':
                print()
                continue

            try:
                print(c.decode('utf-8'), end='')
            except UnicodeDecodeError:
                import util
                print(util.COLOR_INVERTED + '?' + util.COLOR_RESET, end='')

        print("deduction description: {}".format(self.description))
        print("deduction value: {}".format(self.deduction))

        while True:
            ans = input("Should this deduction be taken (y/n)? ")

            if ans in ['y', 'n', 'yes', 'no']:
                break

        if ans == 'y' or ans == 'yes':
            # the deduction *should* be taken, therefore this test fails
            return {'deduction': self.deduction,
                    'description': self.description,
                    'notes': ["failed human review"]}
        else:
            # the deduction *should not* be taken, therefore this test passes
            return None



class DiffTest(BaseTest):

    json_type = 'diff'

    def __init__(self, description, deduction, against):
        import os

        super().__init__(description, deduction)

        if not os.path.isfile(config.static_dir + os.sep + against):
            raise ValueError("solution file for diff ('{}') "
                             "cannot be found".format(against))

        self.against = config.static_dir + os.sep + against


    @staticmethod
    def from_dict(dict_obj, file_type):
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
    supported_tests.append(ReviewTest)


    def run_tests(self):
        results = []
        for t in self.tests:
            result = t.run(self.path)
            if result is not None:
                results.append(result)

        return results


    def __str__(self):
        return self.path + " (plain text file)"
