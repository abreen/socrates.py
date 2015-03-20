from logisim.circuit import Circuit


class LogisimFile:
    def __init__(self, path):
        import xml.etree.ElementTree as ET
        from logisim.parser import from_xml
        from logisim.errors import InvalidWiringError

        tree = ET.parse(path)
        root = tree.getroot()

        circuits = [c for c in root.getchildren() if c.tag == 'circuit']

        objs = []
        broken = []
        for c in circuits:
            name = c.attrib['name']

            try:
                obj = from_xml(root, c)
                objs.append(obj)

            except InvalidWiringError:
                broken.append(name)

        self.circuits = {c.name: c for c in objs}
        self.broken = broken

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
