from logisim.location import Location


class Wire:
    def __init__(self, frm, to):
        self.frm = frm
        self.to = to

    @property
    def frm(self):
        return self._frm

    @frm.setter
    def frm(self, new_frm):
        _check_loc(new_frm)
        self._frm = new_frm

    @property
    def to(self):
        return self._to

    @to.setter
    def to(self, new_to):
        _check_loc(new_to)
        self._to = new_to

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
