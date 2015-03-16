class Location:
    def __init__(self, x_or_obj=None, y=None):
        self.x = 0
        self.y = 0

        if x_or_obj is not None and y is not None:
            if type(x_or_obj) is str:
                x_or_obj = int(x_or_obj)
            if type(y) is str:
                y = int(y)

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

                self.x = int(m.group(1))
                self.y = int(m.group(2))

            elif type(obj) is tuple:
                if len(obj) != 2 or type(obj[0]) is not int or \
                   type(obj[1]) is not int:
                    raise ValueError("tuple must contain two integers")

                self.x, self.y = obj

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, new_x):
        _check_coord(new_x)
        self._x = new_x

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, new_y):
        _check_coord(new_y)
        self._y = new_y

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
        raise ValueError("coordinate must be an integer")

    if coord % 10 != 0:
        raise ValueError("coordinate must be a multiple of 10")

    if coord < 0:
        raise ValueError("coordinate must be positive")
