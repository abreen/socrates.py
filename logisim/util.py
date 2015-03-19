from logisim.location import Location

DIRECTIONS = ['north', 'east', 'south', 'west']


def offset_loc(start, facing, size):
        """Given a Location 'start', a facing direction 'facing', and
        an integer 'size', return the location obtained by starting at
        'start' and traveling 'size' units in the specified facing
        direction. This function assumes that (0, 0) is the northwest
        corner.
        """
        x, y = start.x, start.y

        if facing == 'north':
            y -= size
        elif facing == 'east':
            x += size
        elif facing == 'west':
            x -= size
        else: # self.facing == 'south'
            y += size

        return Location(x, y)


def rotate90(facing):
    dirs = DIRECTIONS + ['north']
    return dirs[dirs.index(facing) + 1]


def rotate180(facing):
    return rotate90(rotate90(facing))


def num_rotations(start, end):
    """Return the number of times required to rotate by 90 degrees
    clockwise from 'start' and end up at 'end'. If the two facing directions
    are equal, this function returns 0.
    """
    m = 0
    while start != end:
        start = rotate90(start)
        m += 1

    return m
