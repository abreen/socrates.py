class Location:

    __slots__ = ['x', 'y']

    def __init__(self, x_or_obj=None, y=None):
        self.x = 0
        self.y = 0

        if x_or_obj is not None and y is not None:
            if type(x_or_obj) is str:
                x_or_obj = int(x_or_obj)
            if type(y) is str:
                y = int(y)

            _check_coord(x_or_obj)
            _check_coord(y)
            self.x, self.y = x_or_obj, y

        elif x_or_obj is not None:
            obj = x_or_obj

            if type(obj) is int:
                raise ValueError("missing Y coordinate")

            if type(obj) is str:
                from re import search
                m = search(r'\(?(\d+), ?(\d+)\)?', obj)
                if not m:
                    raise ValueError("invalid location string: " + repr(obj))

                x = int(m.group(1))
                y = int(m.group(2))

                _check_coord(x)
                _check_coord(y)

                self.x, self.y = x, y

            elif type(obj) is tuple:
                if len(obj) != 2 or type(obj[0]) is not int or \
                   type(obj[1]) is not int:
                    raise ValueError("tuple must contain two integers")

                x, y = obj

                _check_coord(x)
                _check_coord(y)

                self.x, self.y = x, y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return self.x ^ self.y

    def __str__(self):
        return "Location" + repr(self)

    def __repr__(self):
        return '(' + repr(self.x) + ', ' + repr(self.y) + ')'


def _check_coord(coord):
    if type(coord) is not int:
        raise ValueError("coordinate must be an integer: " + str(coord))

    if coord < 0:
        raise ValueError("coordinate must be positive: " + str(coord))
