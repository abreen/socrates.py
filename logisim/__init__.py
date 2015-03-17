from logisim.circuit import Circuit


class LogisimFile:
    def __init__(self, path, lowercase):
        import xml.etree.ElementTree as ET
        from logisim.parser import from_xml

        tree = ET.parse(path)
        root = tree.getroot()

        circuits = [c for c in root.getchildren() if c.tag == 'circuit']
                    #c.attrib['name'] == 'XOR']
                    #c.attrib['name'] == '4-Bit Ripple-Carry Adder']

        circuit_objs = [from_xml(root, c, lowercase) for c in circuits]

        self.circuits = {c.name: c for c in circuit_objs}

    def get_circuit(self, circuit_name):
        try:
            return self.circuits[circuit_name]
        except KeyError:
            return None


def load(path, lowercase=False):
    """Given a path to a Logisim .circ file, return a LogisimFile object
    containing the circuits saved in the .circ file.
    """
    return LogisimFile(path, lowercase)
