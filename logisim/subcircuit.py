from logisim.util import num_rotations
from logisim.errors import NoValueGivenError
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

                try:
                    input_vals[in_pin] = component.eval(at_loc=out_pin_loc)
                except NoValueGivenError:
                    # this subcircuit might still work, if this input pin is
                    # never used in the underlying circuit, so we don't
                    # do anything now
                    continue

            output_vals = self.circuit.eval(input_vals)

            return output_vals[pins[at_loc]]
        else:
            raise NotImplementedError


def _default_subcircuit_locations(subcircuit):
    circuit = subcircuit.circuit

    # for a subcircuit's default appearance, Logisim places each pin on
    # an edge of the subcircuit rectangle by which direction they face in
    # the actual circuit
    pins_facing = {'north': [], 'east': [], 'south': [], 'west': []}

    for pin in circuit.input_pins:
        pins_facing[pin.facing].append(pin)

    for pin in circuit.output_pins:
        pins_facing[pin.facing].append(pin)

    # sort the pins the way Logisim would sort them (for each facing
    # direction, left to right or top to bottom)
    for facing in pins_facing:
        if facing in ['east', 'west']:
            pins_facing[facing].sort(key=lambda pin: pin.loc.y)
        else:
            pins_facing[facing].sort(key=lambda pin: pin.loc.x)

    # we construct a 2D list representing the subcircuit's appearance
    top = pins_facing['south']
    bottom = pins_facing['north']
    left = pins_facing['east']
    right = pins_facing['west']

    # n rows, m columns
    n = max(len(left), len(right))
    m = max(len(top), len(bottom))

    corner_spacing = (top or bottom) and (left or right)

    if corner_spacing:
        m += 2
        n += 2
        top = [None] + top + [None] if top else top
        bottom = [None] + bottom + [None] if bottom else bottom
        left = [None] + left + [None] if left else left
        right = [None] + right + [None] if right else right

    n = max(n, 4)
    m = max(m, 4)

    pin_layout = _make2d(n, m)

    if top:
        _overwrite_row(pin_layout, 0, top)
    if bottom:
        _overwrite_row(pin_layout, n - 1, bottom)
    if left:
        _overwrite_col(pin_layout, 0, left)
    if right:
        _overwrite_col(pin_layout, m - 1, right)

    # we have the subcircuit's location, which is the location of what
    # Logisim calls its "anchor"; by default, the anchor is placed over
    # the first pin facing west (then south, east, and north, if there
    # is no such pin)

    # we will find the position of the anchor pin (the position being its
    # row and column index into the 'pin_layout' 2-D list)
    if len(pins_facing['west']) > 0:
        # pins on the right
        anchor_pos = (1 if corner_spacing else 0, m - 1)

    elif len(pins_facing['south']) > 0:
        # pins on the top
        anchor_pos = (0, 1 if corner_spacing else 0)

    elif len(pins_facing['east']) > 0:
        # pins on the left
        anchor_pos = (1 if corner_spacing else 0, 0)

    elif len(pins_facing['north']) > 0:
        # pins on the bottom
        anchor_pos = (n - 1, 1 if corner_spacing else 0)

    else:
        # TODO subcircuit has no pins?
        pass

    # if this subcircuit is not facing east (the default), rotate the
    # 2-D list and change the anchor position accordingly
    rotations = num_rotations('east', subcircuit.facing)
    if rotations != 0:
        pin_layout, anchor_pos = _rotate(pin_layout, anchor_pos, rotations)

        # redefine: n rows, m columns, if this rotate changed them
        n, m = len(pin_layout), len(pin_layout[0])

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
    row with the values in the new row. If the new row has fewer columns
    than the existing one, the new row is centered and Nones are added
    as padding.
    """
    cols = len(list_[index])

    if cols < len(row):
        raise ValueError("row is too big ({}, expected {})".format(len(row),
                                                                   cols))
    elif cols == len(row):
        new_row = row
    else:
        left = [None] * ((cols - len(row)) // 2)
        right = [None] * (cols - len(row) - len(left))

        new_row = left + row + right

    for c in range(cols):
        list_[index][c] = new_row[c]


def _overwrite_col(list_, index, col):
    """See overwrite_row(). This function does the same thing, but
    column-wise.
    """
    rows = len(list_)

    if rows < len(col):
        raise ValueError("column is too big ({}, expected {})".format(len(col),
                                                                      rows))
    elif rows == len(col):
        new_col = col
    else:
        above = [None] * ((rows - len(col)) // 2)
        below = [None] * (rows - len(col) - len(above))

        new_col = above + col + below

    for r in range(rows):
        list_[r][index] = new_col[r]


def _rotate(pin_layout, anchor_pos, times):
    for n in range(times):
        anchor_pos = _rotate90_pos(anchor_pos, len(pin_layout))
        pin_layout = _rotate90_2d(pin_layout)

    return pin_layout, anchor_pos


def _rotate90_pos(anchor_pos, num_rows):
    row_index, col_index = anchor_pos
    return (col_index, num_rows - row_index - 1)


def _rotate90_2d(list_):
    rows, cols = len(list_), len(list_[0])

    rotated = [[None for _ in range(rows)] for _ in range(cols)]

    for r in range(rows):
        for c in range(cols):
            new_r, new_c = _rotate90_pos((r, c), rows)
            rotated[new_r][new_c] = list_[r][c]

    return rotated
