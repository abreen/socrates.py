from logisim.location import Location

# Logisim's names for component attributes (i.e., the 'a' elements that
# are children of 'tool' or 'comp' elements)
LOGISIM_ATTRIBUTES = ['facing', 'size', 'inputs', 'label', 'loc']


class Component:
    def __init__(self, defaults=None):
        if defaults:
            for key, val in defaults.items():
                setattr(self, key, val)

        self.input_from = {}

    @property
    def loc(self):
        """The location of this component on Logisim's coordinate plane.
        This is stored as a Location object.
        """
        return self._loc

    @loc.setter
    def loc(self, new_loc):
        if type(new_loc) is not Location:
            new_loc = Location(new_loc)

        self._loc = new_loc

    @property
    def input_from(self):
        """A dictionary maintaining, for each input pin on this component,
        the other component that connects to this component and the location
        of the output pin on that other component. Technically, this dict
        contains Location objects corresponding to the locations of input pins
        on this component as keys, and maps the keys to (Component, Location)
        tuples (where, again, the location in the tuple is the location of
        the output pin on the other component).
        """
        return self._input_from

    @input_from.setter
    def input_from(self, new_from):
        _check_dict(new_from)
        self._input_from = new_from

    def eval(self, at_loc):
        """Determine the output of this component by calling the eval()
        methods of components attached to the input pins of this
        component. This component may actually have more than one output
        pin, so 'at_loc' must be specified, and must be the location of
        an output pin on this component.
        """
        raise NotImplementedError

    # subclasses must implement this
    def get_input_locations(self):
        raise NotImplementedError

    # subclasses must implement this
    def get_output_locations(self):
        raise NotImplementedError

    def __repr__(self):
        return self._str_simple()

    def _str_simple(self):
        s = self.__class__.__name__

        if hasattr(self, 'label') and self.label:
            s += " " + repr(self.label)

        s += " at " + repr(self.loc)

        return s

    def __str__(self):
        s = self._str_simple()

        for attr in LOGISIM_ATTRIBUTES:
            if attr in ['label', 'loc']:
                continue

            if hasattr(self, attr):
                s += "\n\t" + attr + ": " + str(getattr(self, attr))

        s += "\n\tinput locations:"
        for loc in self.get_input_locations():
            s += "\n\t\t" + repr(loc)

        s += "\n\toutput locations:"
        for loc in self.get_output_locations():
            s += "\n\t\t" + repr(loc)

        s += "\n\tcomponents connected:"
        for in_pin_loc in self.input_from:
            comp, out_pin_loc = self.input_from[in_pin_loc]
            name = comp.__class__.__name__

            s += "\n\t\t" + name + "'s output pin at " + repr(out_pin_loc) + \
                 " to input pin at " + repr(in_pin_loc)

        return s


def _check_dict(dict_):
    if type(dict_) is not dict:
        raise ValueError("must be a dictionary")

    def valid_item(item):
        k, v = item
        return type(k) is Location and type(v) is tuple and len(v) == 2 and \
               isinstance(v[0], Component) and type(v[1]) is Location

    if not all(map(valid_item, dict_.items())):
        raise ValueError("invalid input component dictionary")

    if not all(map(lambda loc: loc in self.input_locations, dict_)):
        raise ValueError("every location must correspond to the location " +
                         "of an input pin on this component")
