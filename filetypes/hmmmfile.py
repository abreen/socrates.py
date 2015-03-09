from filetypes.plainfile import PlainFile, ReviewTest
from filetypes.basefile import TestSet, BaseFile
from filetypes.basetest import BaseTest
import filetypes
from util import sprint, warn

# for HMMM assembler and simulator
import hmc


def _not_boring(s):
    return s.strip() not in ['', '\t', '\n']

class HMMMEvalTest(BaseTest):
    yaml_type = 'eval'

    def __init__(self, dict_, file_type=None):
        BaseTest.__init__(self, dict_)

        if 'description' not in dict_:
            raise ValueError("HMMM eval test must have a description")

        # store input to program
        # note: this should *not* include a line that turns off debugging
        # since the debugger is switched off by us
        if 'input' in dict_:
            self.input = dict_['input']

        # store expected output; this may be an exact string or a regex
        if 'output' in dict_:
            if type(dict_['output']) is dict and 'match' in dict_['output']:
                import re
                pattern = re.compile(dict_['output']['match'])
                self.output = {'match': pattern}
            else:
                self.output = dict_['output']
        else:
            self.output = None


    def run(self, _):
        import io
        import sys

        sprint("running HMMM test...")

        if self.input is not None:
            in_buf = io.StringIO(self.input)
            sys.stdin = in_buf

        if self.output is not None:
            out_buf = io.StringIO()
            sys.stdout = out_buf

        try:
            hmc.run(self.file.binary_name, debug=False)
        except SystemExit:
            sys.stdin, sys.stdout = sys.__stdin__, sys.__stdout__

            warn("failing test because the simulator exited uncleanly")

            err = filter(_not_boring, out_buf.getvalue().split('\n')[-5:-1])

            return {'deduction': self.deduction,
                    'description': "simluator exited with an error",
                    'notes': err}

        # restore default standard in/out
        sys.stdin, sys.stdout = sys.__stdin__, sys.__stdout__

        if self.output is not None:
            output = out_buf.getvalue()

        passed = True
        if self.output is not None:
            passed = passed and self.__output_matches(output)

        if passed:
            return None
        else:
            result =  {'deduction': self.deduction,
                       'description': self.description,
                       'notes': []}

            if self.output is not None and type(self.output) is str:
                import util
                eo, po = util.escape(self.output), util.escape(output)

                result['notes'].append("expected output: " + eo)
                result['notes'].append("produced output: " + po)

            return result


    def __output_matches(self, out_string):
        if type(self.output) is str:
            return self.output == out_string

        if 'match' in self.output:
            import re
            return self.output['match'].match(out_string)



class HMMMFile(PlainFile):
    yaml_type = 'hmmm'
    extensions = ['hmmm']
    supported_tests = PlainFile.supported_tests.copy()
    supported_tests.append(HMMMEvalTest)


    def __init__(self, dict_):
        BaseFile.__init__(self, dict_)
        # note: the BaseFile constructor handles path, point_value, and
        # initializes tests to []

        # taken if the assembler fails on the HMMM program
        if 'error_deduction' in dict_:
            self.error_deduction = dict_['error_deduction']
        else:
            self.error_deduction = None

        if 'tests' in dict_:
            for t in dict_['tests']:
                test_cls = filetypes.find_test_class(HMMMFile.yaml_type,
                                                     t['type'])
                obj = test_cls(t, HMMMFile.yaml_type)
                obj.file = self
                self.tests.append(obj)


    def run_tests(self):
        """Try to assemble the file using Harvey Mudd's HMMM
        library. If the assembly fails, return the error deduction. If
        the assembly succeeds, attempt to run the program and send it
        the input specified in the criteria file, capturing its output
        to a buffer and comparing it to the expected output.
        """

        import os
        import random
        from functools import reduce

        chars = [str(i) for i in range(10)] + \
                [chr(ord('a') + i) for i in range(26)]

        rand = reduce(str.__add__, [random.choice(chars) for _ in range(32)])
        self.binary_name = rand

        if not hmc.assemble(self.path, self.binary_name):
            return [{'deduction': self.error_deduction,
                     'description': "error assembling '{}'".format(self.path),
                     'notes': ["did not assemble"]}]

        results = []
        for test in self.tests:
            result = test.run(self.path)

            if result is not None:
                results.append(result)

        os.remove(self.binary_name)
        self.binary_name = None

        return results


    def __str__(self):
        return self.path + " (HMMM file)"
