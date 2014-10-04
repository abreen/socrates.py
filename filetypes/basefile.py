import filetypes
from filetypes.basetest import BaseTest


class TestSet(BaseTest):
    yaml_type = 'set'

    def __init__(self, dict_, file_type):
        super().__init__(dict_, file_type)
        self.deductions = dict_['deductions']

        self.members = []
        for m in dict_['members']:
            cls = filetypes.find_test_class(file_type, m['type'])
            self.members.append(cls(m, file_type))


    def __str__(self):
        return "test set"


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
    # the file's type in the YAML file (e.g., 'plain')
    yaml_type = None

    # list of extensions this type uses (e.g., 'txt')
    extensions = None

    # list of test classes that can be used on the file
    supported_tests = [TestSet]


    def __init__(self, dict_):
        self.path = dict_['path']
        self.point_value = dict_['point_value']


    def __str__(self):
        return "{} ({} file)".format(self.path, self.yaml_type)


    def run_tests(self):
        return [t.run() for t in self.tests]
