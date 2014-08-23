import tests
from tests import basetest


class TestSet(basetest.BaseTest):
    handles_type = 'set'

    def __init__(self, target, deductions, members):
        # we don't know the deduction yet, since we have not
        # run the test; the run_test() method will change that
        # we will also refine the description after the test is run
        super().__init__(target, "", 0)

        self.deductions = deductions
        self.members = members


    def __str__(self):
        return "set of tests for {} (map: {}): {}".format(self.target,
                   str(self.deductions), str([str(m) for m in self.members]))


    def to_dict(self):
        test_dict = {'type': self.handles_type,
                     'description': self.description,
                     'deductions': str(self.deductions),
                     'members': [m.to_dict() for m in self.members]}

        return test_dict


    @staticmethod
    def from_dict(dict_obj, test_target):
        if not test_target:
            raise ValueError("the target of this test must be specified")

        args = {'target': test_target,
                'deductions': dict_obj['deductions']}

        members = []
        for m in dict_obj['members']:
            cls = tests.get_test_class(m['type'])
            members.append(cls.from_dict(m, test_target))

        args['members'] = members

        return TestSet(**args)


    def run_test(self, actual_target, context):
        """Run each member test and alter this test's deduction total
        to match the correct deduction from the deduction map. Running this
        function also changes the test's description to include which
        member tests failed.
        """

        num_failures = 0
        for m in self.members:
            passed = m.run_test(actual_target, context)
            if not passed:
                num_failures += 1
                self.description += m.description + '\n'

        self.description = self.description.strip()

        counts = sorted(self.deductions.keys())
        if num_failures < int(counts[0]):
            return True
        else:
            deduction = self.deductions[counts[0]]
            for k in counts:
                if int(k) > num_failures:
                    break
                else:
                    deduction = self.deductions[k]

            self.deduction = deduction

            return False
