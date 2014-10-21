from filetypes.basefile import BaseFile
from filetypes.plainfile import PlainFile
import filetypes

class LogisimFile(PlainFile):
    yaml_type = 'logisim'
    extensions = ['circ']
    supported_tests = PlainFile.supported_tests.copy()

    def __init__(self, dict_):
        BaseFile.__init__(self, dict_)

        if 'tests' in dict_:
            for t in dict_['tests']:
                test_cls = filetypes.find_test_class(LogisimFile.yaml_type,
                                                     t['type'])
                self.tests.append(test_cls(t, LogisimFile.yaml_type))

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
        return self.path + " (Logisim file)"
