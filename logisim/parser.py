"""Tools for interpreting the XML tree contained in a Logisim .circ file."""

# NOTE Logisim (http://www.cburch.com/logisim/) was written
# by Dr. Carl Burch (http://www.cburch.com) and is licensed under the GPL.

from logisim.component import LOGISIM_ATTRIBUTES
from logisim.gates import NOTGate, ANDGate, ORGate
from logisim.pins import InputPin, OutputPin
from logisim.constant import Constant
from logisim.circuit import Circuit
from logisim.subcircuit import Subcircuit
from logisim.wire import Wire
from logisim.location import Location

IGNORED_COMPONENTS = ['Text']


def from_xml(root, circuit_root):
    circuit_name = circuit_root.attrib['name']

    # the wire graph is a mapping from a Location to a list of Wire objects,
    # where a key Location represents an "end" of one or more wires, and the
    # wires with an end at that location are stored in the list
    wire_graph = dict()

    # components are all non-wire objects in the circuit
    components = []
    in_pins, out_pins = [], []

    # create instances of all components in this circuit
    for child in circuit_root:
        if child.tag == 'a':
            continue

        cls = _get_class(child)

        if cls is Wire:
            frm = Location(child.attrib['from'])
            to = Location(child.attrib['to'])

            _add_to_wire_graph(Wire(frm, to), wire_graph)

        elif cls in [NOTGate, ANDGate, ORGate, Constant, InputPin, OutputPin]:
            # if the XML file specified attributes different than the
            # global defaults, we obtain and set them using the constructor
            attrs = _get_all_attributes(child)
            obj = cls(attrs)

            obj.loc = Location(child.attrib['loc'])

            if cls is InputPin:
                in_pins.append(obj)
            elif cls is OutputPin:
                out_pins.append(obj)

            components.append(obj)

        elif cls is Subcircuit:
            name = child.attrib['name']
            circuit_obj = from_xml(root, get_circuit(root, name))

            subcircuit_obj = Subcircuit(circuit_obj)
            subcircuit_obj.loc = Location(child.attrib['loc'])

            components.append(subcircuit_obj)

        else:
            if child.attrib['name'] not in IGNORED_COMPONENTS:
                raise ValueError("unknown component: " + child.attrib['name'])

    # all circuit components are instantiated
    # for each component, find the other component(s) connected to it
    # and add them to the component's 'input_from' dictionary

    for comp in components:
        input_locs = comp.get_input_locations()

        if len(input_locs) == 0:
            # component has no input pins (e.g., a constant)
            continue

        # for each input pin location
        for loc in input_locs:
            # there could be a component at this exact location
            comp_here = _get_comp_at(loc, components)

            if comp_here:
                comp.input_from[loc] = (comp_here, loc)
                continue

            # there's no component here, but there could be wires
            # from here to another component
            if loc not in wire_graph:
                # there are no wires here
                continue

            # there is a wire here; find its source location(s)
            source_locs = _follow_wire(loc, wire_graph)

            # for each source location, find the component at that
            # location, if any
            source_comps = {}
            last_loc = None
            num = 0
            for src_loc in source_locs:
                c = _get_comp_at(src_loc, components)

                if c is not None:
                    last_loc = src_loc
                    num += 1

                source_comps[src_loc] = c

            if num > 1:
                raise ValueError("one pin has multiple inputs")

            elif num == 1:
                # found the one other component that connects to this
                # component at this pin location
                comp.input_from[loc] = (source_comps[last_loc], last_loc)

            else: # num = 0
                # all ends don't connect to any other components
                pass

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
    dictionary's keys are the subclasses of Component defined here
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


def _get_class(el):
    """Given a 'comp' element (a child of a 'circuit' element), a
    a 'tool' element (a child of a 'toolbar' element), or a 'wire' element
    (a child of a 'circuit' element) from a Logisim XML tree, return the
    appropriate subclass of Component that represents the appropriate
    gate, pin, or subcircuit. If the element represents a wire, this
    function returns the Wire class. If the element represents something
    else, None is returned.
    """
    tag = el.tag

    if tag == 'wire':
        return Wire

    name = el.attrib['name']

    if tag in ['comp', 'tool']:
        if 'lib' not in el.attrib:
            # must be user-defined subcircuit
            return Subcircuit

        if 'Gate' in name:
            gate_type = _gate_type(el)
            if gate_type == 'not':
                return NOTGate
            elif gate_type == 'and':
                return ANDGate
            else: # gate_type == 'or'
                return ORGate

        elif name == 'Pin':
            pin_type = _pin_type(el)
            if pin_type == 'input':
                return InputPin
            else: # pin_type == 'output'
                return OutputPin

        elif name == 'Constant':
            return Constant

    return None


def _get_attribute(el, attribute_name, fallback=None):
    """Given either a 'comp' element (a child of a 'circuit' element)
    or a 'tool' element (a child of a 'toolbar' element) from a Logisim
    XML tree, search its attributes (stored as 'a' child elements)
    for the specified attribute (e.g., 'facing'). If the element doesn't
    specify such an attribute, this function returns the fallback
    value, which, when unspecified, is None.
    """
    from re import match
    num_literal_pat = r'^\d+$'
    hex_literal_pat = r'^0x\d+$'

    val = fallback
    for a in el.getchildren():
        if a.attrib['name'] == attribute_name:
            val = a.attrib['val']

            m = match(num_literal_pat, val)
            if m:
                # value is numerical
                val = eval(val)
                break

            m = match(hex_literal_pat, val)
            if m:
                # value is hex (e.g., '0x0')
                val = eval(val, base=16)
                break

            break

    return val


def _get_all_attributes(el):
    """Given either a 'comp' element (a child of a 'circuit' element)
    or a 'tool' element (a child of a 'toolbar' element) from a Logisim
    XML tree, return a dictionary containing its attributes.
    The dictionary's keys are taken from the XML file and should match
    the properties defined in sublcasses of Component.
    Only attributes defined in LOGISIM_ATTRIBUTES are searched for.
    """
    attrs = dict()
    for attr in LOGISIM_ATTRIBUTES:
        a = _get_attribute(el, attr)
        if a is not None:
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


def _follow_wire(end, wire_graph):
    """Given a wire's ending Location and a "wire graph" obtained by parsing
    all the wires in a circuit, "follow" the wire ending at 'end' to
    one or more "sources": that is, the locations(s) where the other end of
    the wire starts. (This function will find sources recursively, in
    the case that a wire reaches an intersection with one or more other
    wires.)
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


def _add_to_wire_graph(wire, wire_graph):
    to, frm = wire.to, wire.frm

    if to not in wire_graph:
        wire_graph[to] = [wire]
    else:
        wire_graph[to].append(wire)

    if frm not in wire_graph:
        wire_graph[frm] = [wire]
    else:
        wire_graph[frm].append(wire)


def _get_comp_at(loc, components):
    """Given a Location and a list of components, return the component
    that has an output pin at that location, or None.
    """
    comps_here = []
    for comp in components:
        if loc in comp.get_output_locations():
            comps_here.append(comp)

    if len(comps_here) > 1:
        raise ValueError("overlapping output pins at this location: " + \
                         str(loc))

    return comps_here[0] if comps_here else None
