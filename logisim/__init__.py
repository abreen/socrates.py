from logisim.parser import Circuit


class LogisimFile:
    def __init__(self, path):
        import xml.etree.ElementTree as ET
        import logisim.parser

        tree = ET.parse(path)
        root = tree.getroot()

        circuits = [c for c in root.getchildren() if c.tag == 'circuit']
        circuit_objs = [logisim.parser.from_xml(root, c) for c in circuits]

        self.circuits = {c.name: c for c in circuit_objs}

    def get_circuit(self, circuit_name):
        try:
            return self.circuits[circuit_name]
        except KeyError:
            return None


def load(path):
    """Given a path to a Logisim .circ file, return a LogisimFile object
    containing the circuits saved in the .circ file.
    """
    return LogisimFile(path)
