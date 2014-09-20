from filetypes.basefile import BaseFile
from filetypes.basetest import BaseTest

from util import sprint, COLOR_BLUE, COLOR_CYAN, COLOR_INVERTED, COLOR_RESET


def _print_file(path):
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
            print(COLOR_INVERTED + '?' + COLOR_RESET, end='')



def _prompt_for(msg, choices):
    from functools import reduce

    while True:
        ans = input("{}{} ({}): {}".format(COLOR_BLUE, msg,
                    reduce(lambda x, y: x + '/' + y,
                           [str(c) for c in choices]),
                    COLOR_RESET))

        for c in choices:
            if ans == str(c):
                return c



class ReviewTest(BaseTest):
    json_type = 'review'

    def __init__(self, description, deduction):
        super().__init__(description, None)

        if type(deduction) is dict:
            if 'choice' not in deduction:
                raise ValueError("missing choice in JSON object")

        self.deduction = {int(k):v for k, v in deduction['choice'].items()}


    def __str__(self):
        return "review of {} ({} pts.)".format(self.target,
                                               self.deduction)


    @staticmethod
    def from_dict(dict_obj, file_type):
        args = {'description': dict_obj['description'],
                'deduction': dict_obj['deduction']}

        return ReviewTest(**args)


    def run(self, path):
        _print_file(path)

        print(COLOR_CYAN + ('-' * 30) + COLOR_RESET)

        if type(self.deduction) is int:
            sprint("deduction description: {}".format(self.description))
            sprint("deduction value: {}".format(self.deduction))

            choice = _prompt_for("should this deduction be taken?",
                                 ['y', 'yes', 'n', 'no'])

            if choice in ['y', 'yes']:
                return {'deduction': self.deduction,
                        'description': self.description,
                        'notes': ["failed human review"]}
            else:
                sprint("taking no deduction")


        if type(self.deduction) is dict:
            sprint("deduction description: {}".format(self.description))
            sprint("deduction options:")

            choices = sorted(self.deduction)
            for k in choices:
                sprint("    -{}: {}".format(k, self.deduction[k]))

            choice = _prompt_for("which deduction should be taken?", choices)

            if choice > 0:
                return {'deduction': choice,
                        'description': self.deduction[choice]}
            else:
                sprint("taking no deduction")


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
