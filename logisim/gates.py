from logisim.errors import NoValueGivenError, NoInputsError
from logisim.debug import narrate
from logisim.util import rotate90, rotate180, offset_loc
from logisim.component import Component


class ANDGate(Component):
    def __init__(self, defaults=None):
        # Logisim global defaults
        self.inputs = 5
        self.size = 50
        self.facing = 'east'

        Component.__init__(self, defaults)

    def get_output_locations(self):
        return [self.loc]

    def get_input_locations(self):
        # using current location, facing direction, and gate size,
        # determine where the inputs start

        # NOTE if the gate is "facing" east, then its input pins are
        # west of the gate's location, since its location refers to its
        # output pin; this is why we use rotate180 here
        offset = offset_loc(self.loc, rotate180(self.facing), self.size)

        # given the size of the gate and the number of inputs, determine
        # the distance between each input pin
        spacing = _gate_spacing(self.size, self.inputs)

        # find the coordinates for each input pin

        # NOTE we use rotate90 here because the input pins are always
        # aligned perpendicular to the axis on which the gate is resting
        locs = _input_locations(offset, rotate90(self.facing),
                                self.inputs, spacing)

        return locs

    def eval(self, at_loc):
        if len(self.input_from) == 0:
            raise NoInputsError

        vals = []
        for _, tup in self.input_from.items():
            component, out_pin_loc = tup

            try:
                vals.append(component.eval(at_loc=out_pin_loc))
            except NoValueGivenError:
                # this gate might still produce a value, so long as
                # there is at least one valid input
                continue

        if not vals:
            raise NoInputsError("AND gate not given any non-error inputs")

        return all(vals)


class ORGate(Component):
    def __init__(self, defaults=None):
        # Logisim global defaults
        self.inputs = 5
        self.size = 50
        self.facing = 'east'

        Component.__init__(self, defaults)

    def get_output_locations(self):
        return [self.loc]

    def get_input_locations(self):
        return ANDGate.get_input_locations(self)

    def eval(self, at_loc):
        if len(self.input_from) == 0:
            raise NoInputsError

        vals = []
        for _, tup in self.input_from.items():
            component, out_pin_loc = tup

            try:
                vals.append(component.eval(at_loc=out_pin_loc))
            except NoValueGivenError:
                # this gate might still produce a value, so long as
                # there is at least one valid input
                continue

        if not vals:
            raise NoInputsError("OR gate not given any non-error inputs")

        return any(vals)


class NOTGate(Component):
    def __init__(self, defaults=None):
        # Logisim global defaults
        # 30 is "wide" (default), 20 is "narrow"
        self.size = 30
        self.facing = 'east'

        Component.__init__(self, defaults)

    def get_output_locations(self):
        return [self.loc]

    def get_input_locations(self):
        return [offset_loc(self.loc, rotate180(self.facing), self.size)]

    def eval(self, at_loc):
        if len(self.input_from) == 0:
            raise NoInputsError

        if len(self.input_from) > 1:
            raise TooManyInputsError

        component, out_pin_loc = list(self.input_from.values())[0]

        return not component.eval(at_loc=out_pin_loc)


def _gate_spacing(size, num_inputs):
    if size == 30:
        return 10

    if size == 50 and num_inputs > 3:
        return 10

    if size == 70 and num_inputs > 4:
        return 10

    if size == 50 and num_inputs <= 3:
        return 20

    if size == 70 and num_inputs in [2, 4]:
        return 20

    if size == 70 and num_inputs == 3:
        return 30


def _input_locations(start, facing, num_inputs, spacing):
    locs = []

    if num_inputs % 2 == 1:
        # there is an input pin at this location
        locs.append(start)

    for i in range(1, (num_inputs // 2) + 1):
        # distance away from "start"
        delta = i * spacing

        locs.append(offset_loc(start, facing, delta))
        locs.append(offset_loc(start, facing, -delta))

    return locs
