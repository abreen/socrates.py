from logisim.debug import narrate
from logisim.component import Component


class Constant(Component):
    def __init__(self, defaults=None):
        # Logisim global defaults
        self.size = 10
        self.facing = 'south'
        self.value = False

        Component.__init__(self, defaults)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_val):
        if new_val not in [0, 1, True, False]:
            raise ValueError("constant value must be 0, 1 or Boolean")

        if type(new_val) is int:
            new_val = bool(new_val)

        self._value = new_val

    def __str__(self):
        return self._str_simple()

    def eval(self, at_loc):
        return self.value

    def get_output_locations(self):
        return [self.loc]

    def get_input_locations(self):
        return []
