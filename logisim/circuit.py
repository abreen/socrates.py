from logisim.debug import narrate
from logisim.errors import NoSuchPinLabelError
from logisim.pins import InputPin, OutputPin


class Circuit:
    def __init__(self, name, input_pins, output_pins):
        self.name = name

        # TODO check that no pins have the same name

        if type(input_pins) is list:
            input_pins = {p.label: p for p in input_pins}

        if type(output_pins) is list:
            output_pins = {p.label: p for p in output_pins}

        self.input_pins = input_pins
        self.output_pins = output_pins

    def __repr__(self):
        return 'Circuit ' + repr(self.name)

    @property
    def input_pins(self):
        return self._input_pins

    @input_pins.setter
    def input_pins(self, new_pins):
        if type(new_pins) is not dict:
            raise ValueError("input pins must be specified in a dict")

        if not all(map(lambda p: type(p) is InputPin, new_pins.values())):
            raise ValueError("all values in dict must be InputPin")

        self._input_pins = new_pins

    @property
    def output_pins(self):
        return self._output_pins

    @output_pins.setter
    def output_pins(self, new_pins):
        if type(new_pins) is not dict:
            raise ValueError("output pins must be specified in a dict")

        if not all(map(lambda p: type(p) is OutputPin, new_pins.values())):
            raise ValueError("all values in dict must be OutputPin")

        self._output_pins = new_pins

    def eval(self, input_dict, pins=False):
        """Given a dictionary mapping input pin labels to Boolean values,
        return a dictionary that maps output pin labels to Boolean
        values, according to the circuit's implementation. Alternatively,
        the input dictionary's keys can be references to InputPin objects
        in this circuit's 'input_pins' dict. (In this case, specifying pins
        by their labels can be avoided.) The optional 'pins' argument, when
        set to True, causes this method to return a dict of OutputPin objects
        to Boolean values, instead of using labels.
        """
        all_pins = []

        for label_or_pin, value in input_dict.items():
            if type(label_or_pin) is str:
                label = label_or_pin

                try:
                    self.input_pins[label].value = value
                    all_pins.append(self.input_pins[label])
                except KeyError:
                    raise NoSuchPinLabelError

            elif type(label_or_pin) is InputPin:
                pin = label_or_pin

                if pin not in self.input_pins.values():
                    raise ValueError("specified an InputPin that is not " + \
                                     "in this circuit")

                pin.value = value
                all_pins.append(pin)

        for pin in self.input_pins.values():
            if pin not in all_pins:
                raise ValueError("not all input pins were given values")

        if pins:
            return {pin: pin.eval() for pin in self.output_pins.values()}
        else:
            return {lab: pin.eval() for lab, pin in self.output_pins.items()}
