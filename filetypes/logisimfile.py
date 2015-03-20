from filetypes.basefile import BaseFile
from filetypes.basetest import BaseTest
from filetypes.plainfile import ReviewTest, PlainFile
import filetypes
from util import sprint, warn, COLOR_RED, COLOR_GREEN
import logisim                          # for parsing Logisim .circ files


class LogisimReviewTest(ReviewTest):
    def __init__(self, dict_, file_type):
        super().__init__(dict_, file_type)

    def run(self, path):
        """A Logisim review test calls the ReviewTest run() method but
        suppresses printing the file. This allows the grader to open the
        file in Logisim and inspect it manually.
        """
        return super().run(path, False)


class EvalTest(BaseTest):
    yaml_type = 'eval'

    def __init__(self, dict_):
        super().__init__(dict_)
        self.input = dict_['input']
        self.output = dict_['output']

        if not self.description:
            _build_description(self.input, self.output)

    def __check_pin_vals(self, dict_):
        if type(dict_) is not dict:
            raise ValueError("pin values must be a dictionary")

        def valid_key(key):
            return type(key) is str

        if not all(map(valid_key, dict_.keys())):
            raise ValueError("pin keys must be strings (pin labels)")

        def valid_val(val):
            return type(val) is bool or (type(val) is int and \
                   val in [0, 1])

        if not all(map(valid_val, dict_.values())):
            raise ValueError("pin values must be Booleans or 0/1")

    @property
    def input(self):
        return self._input

    @input.setter
    def input(self, new_input):
        self.__check_pin_vals(new_input)
        self._input = {k: bool(v) for k, v in new_input.items()}

    @property
    def output(self):
        return self._output

    @output.setter
    def output(self, new_output):
        self.__check_pin_vals(new_output)
        self._output = {k: bool(v) for k, v in new_output.items()}

    def run(self, circuit):
        """Given a logisim.Circuit object, set its input pins, evaluate
        the circuit, and determine if its output matches the expected
        output.
        """
        from logisim.errors import NoInputsError

        sprint("running eval test on '{}'... ".format(circuit.name), end='')

        try:
            output_vals = circuit.eval(self.input)
        except NoInputsError as e:
            sprint("failed", color=COLOR_RED)

            desc = "a component is missing an input value"

            return {'deduction': self.deduction,
                    'description': desc,
                    'notes': [str(e)]}

        failed = False
        for label, value in self.output.items():
            pin = _get_pin_with_label(output_vals.keys(), label)

            if output_vals[pin] != value:
                failed = True
                break

        if failed:
            sprint("failed", color=COLOR_RED)

            desc = _build_description(self.input, self.output).split('\n')
            desc += ["your circuit produced:"]
            desc += _build_description({}, output_vals).split('\n')

            return {'deduction': self.deduction,
                    'description': "did not produce the correct output",
                    'notes': desc}
        else:
            sprint("passed", color=COLOR_GREEN)


class LogisimFile(BaseFile):
    yaml_type = 'logisim'
    extensions = ['circ']
    supported_tests = [LogisimReviewTest, EvalTest]

    def __init__(self, dict_):
        BaseFile.__init__(self, dict_)

        circuits = []
        if 'circuits' in dict_:
            for c in dict_['circuits']:
                cir_obj = LogisimCircuit(c)
                circuits.append(cir_obj)

        self.circuits = circuits

    def run_tests(self):
        from logisim.errors import NoSuchPinLabelError, \
                                   NoValueGivenError, \
                                   DuplicatePinLabelError

        logisim_file = logisim.load(self.path, lowercase=True)
        broken = logisim_file.broken

        results = dict()
        for c in self.circuits:
            results[c] = []

            # check if circuit couldn't be parsed
            if c.name in broken:
                desc = str(c) + " has major wiring issues"

                warn(desc)

                results[c].append({'deduction': c.error_deduction,
                                   'description': desc})
                continue

            circuit = logisim_file.get_circuit(c.name)

            # check if circuit is missing
            if circuit is None:
                warn("missing " + str(c))

                results[c].append({'deduction': c.point_value,
                                   'description': "missing " + str(c)})
                continue

            # check if circuit's output pins have any input
            for pin in circuit.output_pins:
                if len(pin.input_from) > 0:
                    break
            else:
                desc = "output pins of " + str(c) + " are not connected " + \
                       "to anything"

                warn(desc)

                results[c].append({'deduction': c.error_deduction,
                                   'description': desc})
                continue

            # check that the circuit's pins have labels
            without_labels = []
            for pin in circuit.input_pins + circuit.output_pins:
                if not hasattr(pin, 'label'):
                    without_labels.append(repr(pin))

            if without_labels:
                if len(without_labels) == 1:
                    desc = "a pin is missing a label in " + str(c)
                else:
                    desc = "pins are missing labels in " + str(c)

                warn(desc)

                results[c].append({'deduction': c.error_deduction,
                                   'description': desc,
                                   'notes': without_labels})
                continue

            # check that the circuit has the pins we require
            label_errors = []
            for label in c.output_pins:
                try:
                    _ = circuit.get_output_pin(label)
                except NoSuchPinLabelError:
                    label_errors.append("missing " + repr(label) + \
                                        " (output pin)")
                except DuplicatePinLabelError:
                    label_errors.append("duplicate label: " + repr(label))

            for label in c.input_pins:
                try:
                    _ = circuit.get_input_pin(label)
                except NoSuchPinLabelError:
                    label_errors.append("missing " + repr(label) + \
                                        " (input pin)")
                except DuplicatePinLabelError:
                    label_errors.append("duplicate label: " + repr(label))

            if label_errors:
                desc = str(c) + " is missing required pins"

                warn(desc)

                results[c].append({'deduction': c.error_deduction,
                                   'description': desc,
                                   'notes': label_errors})
                continue

            # actually run any tests
            try:
                for t in c.tests:
                    result = t.run(circuit)
                    if result:
                        outer_result = {'description': str(c) + \
                                                       " failed a test"}

                        outer_result['subresults'] = [result]
                        results[c].append(outer_result)

            except NoValueGivenError as e:
                sprint("failed", color=COLOR_RED)

                desc = str(c) + " could not be tested"
                results[c].append({'deduction': c.error_deduction,
                                   'description': desc,
                                   'notes': [str(e)]})

        return [item for subl in results.values() for item in subl]

    def __str__(self):
        return self.path + " (Logisim file)"


class LogisimCircuit:
    """Class representing a specification of a circuit in a criteria file."""

    def __init__(self, dict_):
        self.name = dict_['circuit_name']
        self.input_pins = dict_['input_pins']
        self.output_pins = dict_['output_pins']
        self.point_value = dict_['point_value']
        self.error_deduction = dict_['error_deduction']

        tests = []
        if 'tests' in dict_:
            for t in dict_['tests']:
                cls = filetypes.find_test_class('logisim', t['type'])
                tests.append(cls(t))

        self.tests = tests

    def __str__(self):
        return "circuit " + repr(self.name)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, new_name):
        if type(new_name) is not str or len(new_name) == 0:
            raise ValueError("invalid circuit name")

        self._name = new_name

    @property
    def input_pins(self):
        return self._input_pins

    @input_pins.setter
    def input_pins(self, new_pins):
        self.__check_pins(new_pins, 'input')
        self._input_pins = new_pins

    @property
    def output_pins(self):
        return self._output_pins

    @output_pins.setter
    def output_pins(self, new_pins):
        self.__check_pins(new_pins, 'output')
        self._output_pins = new_pins

    def __check_pins(self, new_pins, type_):
        if type(new_pins) is not list:
            raise ValueError("{} pins must be a list".format(type_))

        if not all(map(lambda p: type(p) is str, new_pins)):
            raise ValueError("{} pin names must be strings".format(type_))

    @property
    def tests(self):
        return self._tests

    @tests.setter
    def tests(self, new_tests):
        def valid_test(t):
            return isinstance(t, filetypes.basetest.BaseTest)

        if not all(map(valid_test, new_tests)):
            raise ValueError("invalid tests: not subclasses of BaseTest")

        self._tests = new_tests

    @property
    def point_value(self):
        return self._point_value

    @point_value.setter
    def point_value(self, new_val):
        if type(new_val) not in [int, float]:
            raise ValueError("invalid point value")

        self._point_value = new_val

    @property
    def error_deduction(self):
        return self._error_deduction

    @error_deduction.setter
    def error_deduction(self, new_val):
        if type(new_val) not in [int, float]:
            raise ValueError("invalid error deduction")

        if new_val > self.point_value:
            raise ValueError("error deduction cannot be greater than the " + \
                             "circuit's point value")

        self._error_deduction = new_val


def _build_description(inputs, outputs):
    in_strs, out_strs = [], []

    if inputs:
        for label, value in inputs.items():
            s = repr(label) + " "
            s += "on" if value else "off"
            in_strs.append(s)

    if outputs:
        for label, value in outputs.items():
            s = repr(label) + " "
            s += "on" if value else "off"
            out_strs.append(s)

    in_strs.sort()
    out_strs.sort()

    if inputs and outputs:
        return "given " + "\nand ".join(in_strs) + ", should output\n" + \
               "\nand ".join(out_strs)
    else:
        return "\n".join(in_strs) + "\n".join(out_strs)


def _get_pin_with_label(pins, label):
    for pin in pins:
        if pin.label == label:
            return pin
    else:
        return None
