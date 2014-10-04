from filetypes.basefile import BaseFile
from filetypes.basetest import BaseTest
import filetypes

from util import sprint, COLOR_BLUE, COLOR_GREEN, COLOR_CYAN, \
                 COLOR_INVERTED, COLOR_RESET


DEDUCTION_MODE_TYPES = [1, '1', '*', '+']

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
        _print_file(path)

        sprint("deduction description: {}".format(self.description))

        if type(self.deduction) is int:
            sprint("deduction value: {}".format(self.deduction))

            while True:
                ans = input(COLOR_CYAN + "should this deduction be "
                            "taken (y/yes/n/no)? " + COLOR_RESET)

                if ans in ['y', 'yes', 'n', 'no']:
                    break

            if ans in ['y', 'yes']:
                return {'deduction': self.deduction,
                        'description': self.description,
                        'notes': ["failed human review"]}
            else:
                sprint("taking no deduction")
                return None

        if type(self.deduction) is list:
            if self.deduction_mode == '*':
                sprint(COLOR_GREEN + "select zero or more:" + COLOR_RESET)
                max, min = float('inf'), 0
            elif self.deduction_mode == '+':
                sprint(COLOR_GREEN + "select one or more:" + COLOR_RESET)
                max, min = float('inf'), 1
            elif self.deduction_mode == '1':
                sprint(COLOR_GREEN + "select one:" + COLOR_RESET)
                max, min = 1, 1

            choices = sorted(self.deduction)
            letters = list(map(lambda x: chr(ord('a') + x), range(len(choices))))

            for i in range(len(choices)):
                sprint("{}. (-{} point{}): {}".format(letters[i],
                       choices[i][0], 's' if choices[i][0] != 1 else '',
                       choices[i][1]))

            num_selections = 0
            selections = []     # unique indices into choices list
            while num_selections < min or num_selections < max:
                sel = input(COLOR_CYAN + "your selection (enter ! "
                            "to stop): " + COLOR_RESET)

                if sel == '!':
                    if num_selections < min:
                        sprint("cannot stop now; you must "
                               "make {} selection{}".format(min,
                               's' if min != 1 else ''), error=True)
                        continue
                    else:
                        break

                try:
                    if letters.index(sel) in selections:
                        sprint("already selected {}".format(sel), error=True)
                        continue

                    selections.append(letters.index(sel))
                    num_selections += 1
                except ValueError:
                    if sel == '':
                        sprint("make a selection, or enter ! to stop",
                               error=True)
                    else:
                        sprint("invalid selection: not in list", error=True)
                    continue

            if sum(map(lambda x: choices[x][0], selections)) > 0:
                deductions = []
                for s in selections:
                    if choices[s][0] > 0:
                        d = {'deduction': choices[s][0],
                             'description': choices[s][1]}
                        deductions.append(d)

                return deductions
            else:
                sprint("taking no deduction(s)")
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
