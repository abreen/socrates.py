from logisim.debug import narrate
from logisim.component import Component
from logisim.errors import NoInputsError, NoValueGivenError


class InputPin(Component):
    def __init__(self, defaults=None):
        # Logisim global defaults
        self.facing = 'east'

        Component.__init__(self, defaults)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_val):
        if new_val not in [0, 1, True, False]:
            raise ValueError("input pin values must be 0, 1 or Boolean")

        if type(new_val) is int:
            new_val = bool(new_val)

        self._value = new_val

    def __str__(self):
        return self._str_simple()

    def eval(self, at_loc):
        try:
            return self.value
        except AttributeError:
            raise NoValueGivenError("input pin was not given a value")

    def get_output_locations(self):
        return [self.loc]

    def get_input_locations(self):
        return []


class OutputPin(Component):
    def __init__(self, defaults=None):
        # Logisim global defaults
        self.facing = 'east'

        Component.__init__(self, defaults)

    def eval(self, at_loc=None):
        """Evaluate this output pin by calling the eval() method on the
        component connected to this pin. The 'at_loc' argument is not
        needed, since the output pin itself has no output pin.
        """
        if len(self.input_from) == 0:
            raise NoInputsError

        if len(self.input_from) > 1:
            raise TooManyInputsError

        component, out_pin_loc = list(self.input_from.values())[0]

        return component.eval(at_loc=out_pin_loc)

    def get_output_locations(self):
        return []

    def get_input_locations(self):
        return [self.loc]
