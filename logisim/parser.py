"""Tools for interpreting the XML tree contained in a Logisim .circ file."""

# note: Logisim (http://www.cburch.com/logisim/) was written
# by Dr. Carl Burch (http://www.cburch.com) and is licensed under the GPL.

# Logisim's names for component attributes (i.e., the 'a' elements that
# are children of 'tool' or 'comp' elements)
LOGISIM_ATTRIBUTES = ['facing', 'size', 'inputs', 'label', 'loc']


def from_xml(root, circuit_root):
    circuit_name = circuit_root.attrib['name']

    # the wire graph is a mapping from (int, int) -> (int, int) where
    # a key (x, y) mapping to (a, b) means that a wire is present starting
    # at (a, b) and ending at (x, y); this allows us to "follow" wires
    # from their endpoints at a particular gate or subcircuit input back to
    # the gate or subcircuit from which it originates
    wire_graph = dict()

    # for non-wire components, like pins and gates
    components = []
    in_pins, out_pins = [], []

    for child in circuit_root:
        cls = _get_class(child)

        if cls is Wire:
            frm = _parse_location_string(child.attrib['from'])
            to = _parse_location_string(child.attrib['to'])

            obj = cls(frm, to)

            if to not in wire_graph:
                wire_graph[to] = [obj]
            else:
                wire_graph[to].append(obj)

            if frm not in wire_graph:
                wire_graph[frm] = [obj]
            else:
                wire_graph[frm].append(obj)

        elif cls in [NOTGate, ANDGate, ORGate, InputPin, OutputPin]:
            # if the XML file specified attributes different than the
            # global defaults, we obtain and set them using the constructor
            attrs = _get_all_attributes(child)
            obj = cls(attrs)
            obj.loc = child.attrib['loc']

            if cls is InputPin:
                in_pins.append(obj)
            elif cls is OutputPin:
                out_pins.append(obj)

            components.append(obj)

        elif cls is Subcircuit:
            # this object in this circuit is another, user-constructed
            # circuit; we will call this function on its circuit root
            # to get a Circuit object representing it

            # TODO this could be memory inefficient, because we may be
            # duplicating Circuits many times (recursively)

            # TODO
            #subcircuit = from_xml(root, get_circuit(root, name))
            pass

    # all circuit components are instantiated
    # for each component with any input pins, "follow" any wires ending
    # at the location of those pins to the gate or pin that is its source
    for comp in components:
        if type(comp) is InputPin:
            # has no input wires
            continue

        for loc in comp.get_input_locations():
            if loc in wire_graph:
                # there is a wire here; find its source locations
                source_locs = _follow_wire(loc, wire_graph)

                source_comps = []
                for source_loc in source_locs:
                    for other_comp in components:
                        if other_comp is comp:
                            continue

                        if source_loc == other_comp.loc:
                            # an output pin of another component is here
                            source_comps.append(other_comp)

                if len(source_comps) > 1:
                    raise ValueError("one pin has multiple inputs")
                elif len(source_comps) == 1:
                    comp.input_components.append(source_comps[0])
                # else: all ends of the wire don't connect to another component

    return Circuit(circuit_name, in_pins, out_pins)


def get_circuit(root, circuit_name):
    """Given the root of a Logisim XML tree and the name of a
    user-constructed circuit in that tree, return the root of the circuit
    tree, or None if no circuit by that name could be found.
    """
    for child in root:
        if child.tag == 'circuit' and child.attrib['name'] == circuit_name:
            return child

    return None


def get_defaults(root):
    """Given the root of a Logisim XML tree, consult its 'toolbar' elements
    to obtain a dictionary of default attributes for gates and pins. This
    dictionary's keys are the subclasses of LogisimObject defined here
    (e.g., ANDGate) and the values are dicts mapping attributes (e.g.,
    'facing') to their default values defined in this Logisim file. If a
    default mapping is empty, the global Logisim defaults should be used
    (these are defined in each class as class attributes).
    """
    defaults = dict()
    toolbar = root.find('toolbar')

    for tool in toolbar:
        if tool.tag == 'sep':
            continue

        cls = _get_class(tool)
        if cls in [Subcircuit, None]:
            continue

        defaults[cls] = _get_all_attributes(tool)

    return defaults


class Circuit:
    def __init__(self, name, input_pins, output_pins):
        self.name = name
        self.input_pins = {pin.label: pin for pin in input_pins}
        self.output_pins = {pin.label: pin for pin in output_pins}

    def eval(self, input_dict):
        """Given a dictionary mapping input pin names to Boolean values,
        return a dictionary that maps output pin names to Boolean
        values, according to the circuit's implementation.
        """
        for label, value in input_dict.items():
            self.input_pins[label].value = value

        return {label: pin.eval() for label, pin in self.output_pins.items()}


class LogisimObject:
    def __init__(self, defaults=None):
        if defaults:
            for key, val in defaults.items():
                setattr(self, key, val)

        self.input_components = []

    def __str__(self):
        s = self.__class__.__name__
        s += " at " + str(self.loc) + '\n'

        for attr in LOGISIM_ATTRIBUTES:
            if attr == 'loc':
                continue

            if hasattr(self, attr):
                s += '\t' + attr + ' = ' + repr(getattr(self, attr)) + '\n'

        if len(self.input_components) > 0:
            s += '\tinput_components =\n'
            for comp in self.input_components:
                cls_name = comp.__class__.__name__
                loc = comp.loc
                s += '\t\t' + cls_name + " at " + repr(loc) + '\n'

        input_locs = self.get_input_locations()
        if input_locs is not None:
            s += '\tinput_locations =\n'
            for loc in input_locs:
                s += '\t\t' + repr(loc) + '\n'

        return s

    def __repr__(self):
        return str(self)

    @property
    def loc(self):
        return self._loc

    @loc.setter
    def loc(self, new_loc):
        if type(new_loc) is not tuple:
            new_loc = _parse_location_string(new_loc)

        if type(new_loc[0]) is not int or type(new_loc[1]) is not int:
            raise ValueError("position coordinates must be integers")

        self._loc = new_loc

    @property
    def input_components(self):
        return self._input_components

    @input_components.setter
    def input_components(self, new_components):
        if type(new_components) is not list:
            raise ValueError("invalid components: not a list")

        def valid_comp(comp):
            return isinstance(comp, LogisimObject)

        if not all(map(valid_comp, new_components)):
            raise ValueError("all components must be LogisimObjects")

        self._input_components = new_components

    def get_input_locations(self):
        """Return a list of (x, y) coordinate pairs corresponding to the
        locations of the input pins for this gate. If this LogisimObject
        represents an InputPin, this method returns None. The number of
        pairs returned by this method should be equal to this object's
        'num_inputs' attribute.
        """
        locs = []
        x, y = self.loc

        if type(self) in [ANDGate, ORGate]:
            num_inputs = self.inputs
            size = self.size
        elif type(self) is NOTGate:
            num_inputs = 1
            size = self.size
        elif type(self) is OutputPin:
            return [self.loc]
        else:
            # should be InputPin
            return None

        if self.facing == 'north':
            y -= size
        elif self.facing == 'east':
            x -= size
        elif self.facing == 'west':
            x += size
        else: # self.facing == 'south'
            y += size

        yd = _ydiff(size, num_inputs)
        n = num_inputs // 2

        if num_inputs % 2 == 1:
            # there is an input pin at this location
            locs.append((x, y))

        for i in range(1, n + 1):
            d = i * yd
            locs.append((x, y + d))
            locs.append((x, y - d))

        return locs


class ANDGate(LogisimObject):
    inputs = 5
    size = 50
    facing = 'east'

    def __init__(self, defaults=None):
        LogisimObject.__init__(self, defaults)

    def eval(self):
        return all([g.eval() for g in self.input_components])


class ORGate(LogisimObject):
    inputs = 5
    size = 50
    facing = 'east'

    def __init__(self, defaults=None):
        LogisimObject.__init__(self, defaults)

    def eval(self):
        return any([g.eval() for g in self.input_components])


class NOTGate(LogisimObject):
    # 30 is "wide" (default), 20 is "narrow"
    size = 30
    facing = 'east'

    def __init__(self, defaults=None):
        LogisimObject.__init__(self, defaults)

    def eval(self):
        if len(self.input_components) > 1:
            raise ValueError("NOT gate has more than one input")

        return not self.input_components[0].eval()


class InputPin(LogisimObject):
    facing = 'east'

    def __init__(self, defaults=None):
        LogisimObject.__init__(self, defaults)

    def eval(self):
        return self.value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        if type(new_value) is not bool:
            raise ValueError("input pin values must be Boolean")

        self._value = new_value


class OutputPin(LogisimObject):
    facing = 'west'

    def __init__(self, defaults=None):
        LogisimObject.__init__(self, defaults)

    def eval(self):
        if len(self.input_components) > 1:
            raise ValueError("output pin has more than one input")

        return self.input_components[0].eval()


class Subcircuit(LogisimObject):
    pass


class Wire:
    def __init__(self, frm, to):
        self.frm = frm
        self.to = to

    def __str__(self):
        return 'wire at ' + repr(self.frm) + ' and ' + repr(self.to)

    def __repr__(self):
        return str(self)

    def other_end(self, end):
        if end == self.frm:
            return self.to
        elif end == self.to:
            return self.frm
        else:
            raise ValueError("this wire does not have an end at " + repr(end))

    @property
    def frm(self):
        return self._frm

    @frm.setter
    def frm(self, new_frm):
        if type(new_frm) is not tuple:
            new_frm = _parse_location_string(new_frm)

        if type(new_frm[0]) is not int or type(new_frm[1]) is not int:
            raise ValueError("position coordinates must be integers")

        self._frm = new_frm

    @property
    def to(self):
        return self._to

    @to.setter
    def to(self, new_to):
        if type(new_to) is not tuple:
            new_to = _parse_location_string(new_to)

        if type(new_to[0]) is not int or type(new_to[1]) is not int:
            raise ValueError("position coordinates must be integers")

        self._to = new_to


def _get_attribute(el, attribute_name, fallback=None):
    """Given either a 'comp' element (a child of a 'circuit' element)
    or a 'tool' element (a child of a 'toolbar' element) from a Logisim
    XML tree, search its attributes (stored as 'a' child elements)
    for the specified attribute (e.g., 'facing'). If the element doesn't
    specify such an attribute, this function returns the fallback
    value, which, when unspecified, is None.
    """
    val = fallback
    for a in el.getchildren():
        if a.attrib['name'] == attribute_name:
            val = a.attrib['val']
            break

    return val


def _get_all_attributes(el):
    """Given either a 'comp' element (a child of a 'circuit' element)
    or a 'tool' element (a child of a 'toolbar' element) from a Logisim
    XML tree, return a dictionary containing its attributes.
    The dictionary's keys are taken from the XML file and should match
    the properties defined in sublcasses of LogisimObject.
    Only attributes defined in LOGISIM_ATTRIBUTES are searched for.
    """
    from re import match
    num_pat = r'^\d+$'

    attrs = dict()
    for attr in LOGISIM_ATTRIBUTES:
        a = _get_attribute(el, attr)
        if a is not None:
            m = match(num_pat, a)
            if m:
                # value is numerical
                attrs[attr] = eval(a)
            else:
                attrs[attr] = a

    return attrs


def _pin_type(el):
    """Given either a 'comp' element (a child of a 'circuit' element)
    or a 'tool' element (a child of a 'toolbar' element) from a Logisim
    XML tree that represents a pin, return its type
    (i.e., either 'output' or 'input').
    """
    is_output = _get_attribute(el, 'output', 'false')
    return 'output' if is_output == 'true' else 'input'


def _gate_type(el):
    """Given either a 'comp' element (a child of a 'circuit' element)
    or a 'tool' element (a child of a 'toolbar' element) from a Logisim
    XML tree that represents a gate, return the gate's type (i.e., one
    of 'not', 'and', and 'or').
    """
    name = el.attrib['name']

    if name == 'NOT Gate':
        return 'not'
    elif name == 'AND Gate':
        return 'and'
    elif name == 'OR Gate':
        return 'or'

    raise ValueError("invalid or unknown gate type: " + name)


def _get_class(el):
    """Given a 'comp' element (a child of a 'circuit' element), a
    a 'tool' element (a child of a 'toolbar' element), or a 'wire' element
    (a child of a 'circuit' element) from a Logisim XML tree, return the
    appropriate subclass of LogisimObject that represents the appropriate
    gate, pin, or subcircuit. If the element represents a wire, this
    function returns the Wire class. If the element represents something
    else, None is returned.
    """
    if el.tag == 'wire':
        return Wire

    if el.tag in ['comp', 'tool']:
        if 'lib' not in el.attrib:
            # must be user-defined subcircuit
            return Subcircuit

        if 'Gate' in el.attrib['name']:
            gate_type = _gate_type(el)
            if gate_type == 'not':
                return NOTGate
            elif gate_type == 'and':
                return ANDGate
            else: # gate_type == 'or'
                return ORGate

        elif el.attrib['name'] == 'Pin':
            pin_type = _pin_type(el)
            if pin_type == 'input':
                return InputPin
            else: # pin_type == 'output'
                return OutputPin

    return None


def _ydiff(size, num_inputs):
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


def _parse_location_string(loc):
    from re import search
    m = search(r'\((\d+), ?(\d+)\)', loc)
    if not m:
        raise ValueError("invalid location string: " + repr(loc))
    return int(m.group(1)), int(m.group(2))


def _follow_wire(end, wire_graph):
    """Given a wire's ending location (a tuple of two integers representing
    a location on Logisim's grid) and a "wire graph" obtained by parsing
    all the wires in a circuit, "follow" the wire ending at 'end' to
    one or more "sources": that is, the locations(s) where the other end of
    the wire starts. (This function will find sources recursively, in
    the case that a wire reaches an intersection with one or more other
    wires.) Note: if not exactly one source returned by this function shares
    its location with an output pin, then the circuit is buggy, since two
    outputs are sharing wires without a gate to reduce them.
    """
    sources = []
    seen_wires = []
    queue = []
    queue.append(end)
    while len(queue) > 0:
        loc = queue.pop(0)

        if loc != end and len(wire_graph[loc]) == 1:
            # found a source
            sources.append(loc)
            continue

        for wire in wire_graph[loc]:
            if wire in seen_wires:
                continue

            seen_wires.append(wire)
            other_end = wire.other_end(loc)
            queue.append(other_end)

    return sources

def _print_components(comps):
    for c in comps:
        print(c)
