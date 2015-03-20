from logisim.location import Location


class Wire:
    """Class representing a single wire drawn on a Logisim coordinate
    plane. Wires in Logisim are always vertical or horizontal.
    Two wires are connected when they share a 'frm' (from) or 'to'
    coordinate.
    """

    __slots__ = ['frm', 'to']

    def __init__(self, frm, to):
        _check_loc(frm)
        _check_loc(to)
        self.frm = frm
        self.to = to

    def __str__(self):
        return 'wire at ' + repr(self.frm) + ' and ' + repr(self.to)

    def other_end(self, end):
        if end == self.frm:
            return self.to
        elif end == self.to:
            return self.frm
        else:
            raise ValueError("this wire does not have an end at " + repr(end))


def _check_loc(loc):
    if type(loc) is not Location:
        raise ValueError("location must be a Location object")
