from abc import ABCMeta, abstractmethod

import filetypes
from filetypes.basetest import BaseTest


class TestSet(BaseTest):
    json_type = 'set'

    def __init__(self, deductions, members):
        super().__init__("", 0)

        self.deductions = deductions
        self.members = members


    def __str__(self):
        return "test set"


    def to_dict(self):
        test_dict = {'description': self.description,
                     'deductions': str(self.deductions),
                     'members': [m.to_dict() for m in self.members]}

        return test_dict


    @staticmethod
    def from_dict(dict_obj):
        args = {'deductions': dict_obj['deductions']}

        members = []
        for m in dict_obj['members']:
            cls = filetypes.find_test_class(m['type'])
            members.append(cls.from_dict(m))

        args['members'] = members

        return TestSet(**args)


    def run(self, context):
        """Run each member test and alter this test's deduction total
        to match the correct deduction from the deduction map. Running this
        function also changes the test's description to include which
        member tests failed.
        """

        failed_tests = []
        for m in self.members:
            failed = m.run(context)
            if failed:
                failed_tests.append(failed)

        counts, nf = sorted(self.deductions.keys()), len(failed_tests)
        if nf < int(counts[0]):
            return None
        else:
            deduction = self.deductions[counts[0]]
            for k in counts:
                if int(k) > nf:
                    break
                else:
                    deduction = self.deductions[k]

            self.deduction = deduction

            desc = "failed {} test{}:".format(nf, 's' if nf != 1 else '')
            for t in failed_tests:
                del t['deduction']

            return  {'deduction': deduction,
                     'description': desc,
                     'subresults': failed_tests}



class BaseFile:
    __metaclass__ = ABCMeta

    # the file's type in the JSON object (e.g., 'plain')
    json_type = None

    # list of extensions this type uses (e.g., 'txt') (not currently used)
    extensions = None

    # list of test classes that can be used on the file
    supported_tests = [TestSet]


    def __init__(self, path, point_value, tests=None):
        self.path = path
        self.point_value = point_value
        self.tests = tests if tests else []


    @classmethod
    def from_dict(cls, dict_obj):
        args = {'path': dict_obj['path'],
                'point_value': dict_obj['point_value'],
                'tests': []}

        if 'tests' in dict_obj:
            for t in dict_obj['tests']:
                test_cls = filetypes.find_test_class(t['type'])
                if test_cls not in cls.supported_tests:
                    raise ValueError("file type '{}' does not support"
                                     "test type '{}'".format(cls.json_type,
                                     t['type']))

                args['tests'].append(test_cls.from_dict(t))

        return cls(**args)


    def to_dict(self):
        return {'path': self.path,
                'type': self.json_type,
                'point_value': self.point_value,
                'tests': [t.to_dict() for t in self.tests]}


    def run_tests(self):
        return [t.run() for t in self.tests]


    def __str__(self):
        return "{} ({} file)".format(self.path, self.json_type)
