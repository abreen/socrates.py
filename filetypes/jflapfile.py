from filetypes.basefile import BaseFile
from filetypes.plainfile import PlainFile
from filetypes.plainfile import ReviewTest
import filetypes

class JFLAPReviewTest(ReviewTest):
    def __init__(self, dict_, file_type):
        super().__init__(dict_, file_type)

    def run(self, path):
        """A JFLAP review test calls the ReviewTest run() method but
        suppresses printing the file.
        """
        return super().run(path, False)



class JFLAPFile(PlainFile):
    yaml_type = 'jflap'
    extensions = ['jff']
    supported_tests = PlainFile.supported_tests.copy()
    supported_tests.append(JFLAPReviewTest)

    def __init__(self, dict_):
        BaseFile.__init__(self, dict_)

        if 'tests' in dict_:
            for t in dict_['tests']:
                test_cls = filetypes.find_test_class(JFLAPFile.yaml_type,
                                                     t['type'])
                self.tests.append(test_cls(t, JFLAPFile.yaml_type))

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
        return self.path + " (JFLAP file)"
