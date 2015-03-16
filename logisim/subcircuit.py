from logisim.debug import narrate, suppress_narration
from logisim.location import Location
from logisim.component import Component
from logisim.pins import InputPin, OutputPin


class Subcircuit(Component):
    def __init__(self, circuit, defaults=None):
        # Logisim global defaults
        self.facing = 'east'

        Component.__init__(self, defaults)

        # reference to Circuit object
        self.circuit = circuit

        self.label = circuit.name

        # TODO custom subcircuit appearance
        self.appearance = None

    def get_output_locations(self):
        """Use the underlying Circuit object's appearance data
        (or the default logic) to produce a list of output pin locations.
        """
        if not self.appearance:
            locs = _default_subcircuit_locations(self)
            return [loc for loc, pin in locs.items() if type(pin) is OutputPin]
        else:
            raise NotImplementedError

    def get_input_locations(self):
        """Use the underlying Circuit object's appearance data
        (or the default logic) to produce a list of input pin locations.
        """
        if not self.appearance:
            locs = _default_subcircuit_locations(self)
            return [loc for loc, pin in locs.items() if type(pin) is InputPin]
        else:
            raise NotImplementedError

    def get_pin_at(self, loc):
        """Given the location of a pin on this subcircuit, return
        the pin at that location. This method produces the location of the
        pin on this subcircuit's representation, not the location of the pin
        on the underlying circuit's coordinate plane.
        """
        if not self.appearance:
            locs = _default_subcircuit_locations(self)
        else:
            raise NotImplementedError

        for pin_loc, pin in locs.items():
            if pin_loc == loc:
                return pin

        return None

    def eval(self, at_loc):
        if not self.appearance:
            pins = _default_subcircuit_locations(self)

            input_vals = {}
            for in_pin_loc, tup in self.input_from.items():
                component, out_pin_loc = tup

                in_pin = pins[in_pin_loc]
                input_vals[in_pin] = component.eval(at_loc=out_pin_loc)

            output_vals = self.circuit.eval(input_vals, pins=True)

            return output_vals[pins[at_loc]]
        else:
            raise NotImplementedError


def _default_subcircuit_locations(subcircuit):
    circuit = subcircuit.circuit

    # for a subcircuit's default appearance, Logisim places each pin on
    # an edge of the subcircuit rectangle by which direction they face in
    # the actual circuit
    pins_facing = {'north': [], 'east': [], 'south': [], 'west': []}

    for pin in circuit.input_pins.values():
        pins_facing[pin.facing].append(pin)

    for pin in circuit.output_pins.values():
        pins_facing[pin.facing].append(pin)

    # sort the pins the way Logisim would sort them (for each facing
    # direction, left to right or top to bottom)
    for facing in pins_facing:
        if facing in ['east', 'west']:
            pins_facing[facing].sort(key=lambda pin: pin.loc.y)
        else:
            pins_facing[facing].sort(key=lambda pin: pin.loc.x)

    # we have the subcircuit's location, which is the location of what
    # Logisim calls its "anchor"; by default, the anchor is placed over
    # the first pin facing west (then south, east, and north, if there
    # is no such pin)
    if len(pins_facing['west']) > 0:
        anchor = 'west'
    elif len(pins_facing['south']) > 0:
        anchor = 'south'
    elif len(pins_facing['east']) > 0:
        anchor = 'east'
    elif len(pins_facing['north']) > 0:
        anchor = 'north'
    else:
        # circuit actually has no pins
        return []

    # we construct a 2D list representing the subcircuit's appearance
    top = [None] + pins_facing['south'] + [None]
    bottom = [None] + pins_facing['north'] + [None]
    left = [None] + pins_facing['east'] + [None]
    right = [None] + pins_facing['west'] + [None]

    # n rows, m columns
    n = max(4, max(len(left), len(right)))
    m = max(4, max(len(top), len(bottom)))

    pin_layout = _make2d(n, m)

    _overwrite_row(pin_layout, 0, top)
    _overwrite_row(pin_layout, n - 1, bottom)
    _overwrite_col(pin_layout, 0, left)
    _overwrite_col(pin_layout, m - 1, right)

    # determine position of anchor in pin_layout
    if anchor == 'west':
        anchor_pos = (1, m - 1)
    elif anchor == 'south':
        anchor_pos = (0, 1)
    elif anchor == 'east':
        anchor_pos = (1, 0)
    else: # anchor == 'north'
        anchor_pos = (n - 1, 1)

    x, y = subcircuit.loc.x, subcircuit.loc.y

    # finds location of each pin given the subcircuit's anchor
    # position by finding each position's difference in position
    # in the list, and using that to find its absolute position
    def pin_location(val, row, col):
        y_offset = row - anchor_pos[0]
        x_offset = col - anchor_pos[1]
        return Location(x + (x_offset * 10), y + (y_offset * 10))

    pin_locs = _map2d(pin_location, pin_layout)

    return {pin_locs[r][c]: pin_layout[r][c]
            for r in range(n) for c in range(m)
            if type(pin_layout[r][c]) is not None}


def _map2d(f, list2d):
    new_list2d = []

    for r in range(len(list2d)):
        new_row = []
        for c in range(len(list2d[r])):
            new_row.append(f(list2d[r][c], r, c))

        new_list2d.append(new_row)

    return new_list2d


def _make2d(rows, cols):
    return [[None for _ in range(cols)] for _ in range(rows)]


def _overwrite_row(list_, index, row):
    """Given a reference to a 2-D list and a row index, replace the
    row with the values in the given row, starting from the left.
    The length of the new row can be less than the existing row;
    the old values in that row will remain.
    """
    for c in range(len(row)):
        list_[index][c] = row[c]


def _overwrite_col(list_, index, col):
    """Given a reference to a 2-D list and a column index, replace the
    column with the values in the given row, starting from the top.
    The length of the new column can be less than the existing one;
    the old values in that column will remain.
    """
    for r in range(len(col)):
        list_[r][index] = col[r]
