from filetypes.basefile import BaseFile
from filetypes.plainfile import PlainFile
import filetypes

class JFLAPFile(PlainFile):
    yaml_type = 'jflap'
    extensions = ['jff']
    supported_tests = PlainFile.supported_tests.copy()

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
