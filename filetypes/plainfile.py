from filetypes.basefile import BaseFile
from filetypes.basetest import BaseTest
import filetypes
import prompt

from util import sprint, plural, COLOR_BLUE, COLOR_GREEN, COLOR_CYAN, \
                 COLOR_INVERTED, COLOR_RESET


DEDUCTION_MODE_TYPES = prompt.PROMPT_MODES

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



class ReviewTest(BaseTest):
    yaml_type = 'review'

    def __init__(self, dict_, file_type):
        super().__init__(dict_, file_type)

        if type(dict_['deduction']) is dict:
            mode, deductions = dict_['deduction'].popitem()
            if mode not in DEDUCTION_MODE_TYPES:
                raise ValueError("invalid deduction mode '{}' in criteria; "
                                 "should be one of {}".format(mode,
                                 DEDUCTION_MODE_TYPES))

            self.deduction = []
            for d in deductions:
                value, reason = d.popitem()
                value = int(value)

                self.deduction.append((value, reason))

            self.deduction_mode = mode

        else:
            self.deduction = dict_['deduction']


    def __str__(self):
        return "review of {} ({} pts.)".format(self.target,
                                               self.deduction)


    def run(self, path):
        from functools import reduce
        import prompt
        _print_file(path)

        sprint("reviewing '{}' (in directory '{}')".format(
               path, os.getcwd()))
        sprint("description: " + self.description)

        if type(self.deduction) is int:
            choices = ["do not take this deduction",
                       "take this deduction (-{} points)".format(
                           self.deduction)]
            got = prompt.prompt(choices, '1')

            if got == [1]:
                return {'deduction': self.deduction,
                        'description': self.description}
            else:
                sprint("taking no points")
                return None

        elif type(self.deduction) is list:
            choices = ["{} (-{} {})".format(y, x, plural("point", x)) for
                       x, y in self.deduction]
            got = prompt.prompt(choices, self.deduction_mode)

            if sum(map(lambda x: self.deduction[x][0], got)) > 0:
                deductions = []

                for s in got:
                    if self.deduction[s][0] > 0:
                        d = {'deduction': self.deduction[s][0],
                             'description': self.deduction[s][1]}
                        deductions.append(d)

                return deductions
            else:
                sprint("taking no points")
                return None



class DiffTest(BaseTest):
    yaml_type = 'diff'

    def __init__(self, dict_, file_type):
        import os

        super().__init__(dict_, file_type)

        if not os.path.isfile(config.static_dir + os.sep + dict_['against']):
            raise ValueError("solution file for diff ('{}') "
                             "cannot be found".format(dict_['against']))

        self.against = config.static_dir + os.sep + dict_['against']


    def run(self, submission):
        import filecmp

        if filecmp.cmp(submission, self.against):
            return None
        else:
            return {'deduction': self.deduction,
                    'description': self.description,
                    'notes': ["files do not match"]}



class PlainFile(BaseFile):
    yaml_type = 'plain'
    extensions = ['txt']
    supported_tests = BaseFile.supported_tests.copy()
    supported_tests.append(DiffTest)
    supported_tests.append(ReviewTest)

    def __init__(self, dict_):
        BaseFile.__init__(self, dict_)

        if 'tests' in dict_:
            for t in dict_['tests']:
                test_cls = filetypes.find_test_class(PlainFile.yaml_type,
                                                     t['type'])
                self.tests.append(test_cls(t, PlainFile.yaml_type))

    def run_tests(self):
        results = []
        for t in self.tests:
            result = t.run(self.path)

            if result:
                if type(result) is list:
                    for r in result:
                        results.append(r)
                else:
                    results.append(result)

        return results


    def __str__(self):
        return self.path + " (plain text file)"
