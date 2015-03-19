from logisim.debug import narrate
from logisim.errors import NoSuchPinLabelError, DuplicatePinLabelError
from logisim.pins import InputPin, OutputPin


class Circuit:
    def __init__(self, name, input_pins, output_pins):
        self.name = name
        self.input_pins = input_pins
        self.output_pins = output_pins

    def __repr__(self):
        return 'Circuit ' + repr(self.name)

    @property
    def input_pins(self):
        return self._input_pins

    @input_pins.setter
    def input_pins(self, new_pins):
        _check_pins(new_pins, InputPin)
        self._input_pins = new_pins

    @property
    def output_pins(self):
        return self._output_pins

    @output_pins.setter
    def output_pins(self, new_pins):
        _check_pins(new_pins, OutputPin)
        self._output_pins = new_pins

    def get_input_pin(self, label):
        pins = []
        for pin in self.input_pins:
            if pin.label == label:
                pins.append(pin)

        if len(pins) == 0:
            raise NoSuchPinLabelError
        elif len(pins) == 1:
            return pins[0]
        else:
            raise DuplicatePinLabelError(label)

    def get_output_pin(self, label):
        pins = []
        for pin in self.output_pins:
            if pin.label == label:
                pins.append(pin)

        if len(pins) == 0:
            raise NoSuchPinLabelError
        elif len(pins) == 1:
            return pins[0]
        else:
            raise DuplicatePinLabelError(label)

    def eval(self, input_dict):
        """Given a dictionary mapping input pin labels to Boolean values,
        return a dictionary that maps output pins to their Boolean
        values, according to the circuit's implementation. Alternatively,
        the input dictionary's keys can be references to InputPin objects
        in this circuit's 'input_pins' dict. (In this case, specifying pins
        by their labels can be avoided.)
        """
        for label_or_pin, value in input_dict.items():
            if type(label_or_pin) is str:
                label = label_or_pin

                self.get_input_pin(label).value = value

            elif type(label_or_pin) is InputPin:
                pin = label_or_pin

                if pin not in self.input_pins:
                    raise ValueError("specified an InputPin that is not " + \
                                     "in this circuit")

                pin.value = value

        return {pin: pin.eval() for pin in self.output_pins}


def _check_pins(pins, type_):
    if type(pins) is not list:
        raise ValueError("pins must be specified in a list")

    if not all(map(lambda p: type(p) is type_, pins)):
        raise ValueError("all values in list must be " + type_.__name__)
