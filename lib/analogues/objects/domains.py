import os

DOMAINS = {}


class Domain:

    def __init__(self, name, north, west, south, east):
        self.title = name
        self.name = name
        self.north = north
        self.south = south
        self.east = east
        self.west = west

    @classmethod
    def lookup(cls, name):
        return DOMAINS[name]

    def to_mars(self, request):
        request['area'] = "%s/%s/%s/%s" % (
            self.north,
            self.west,
            self.south,
            self.east,
        )

        request['grid'] = "0.5/0.5"

    @property
    def area(self):
        return [self.north,
                self.west,
                self.south,
                self.east]


DOMAINS['uk'] = Domain('uk', 60, -14, 44.5, 1.5)
DOMAINS['france'] = Domain('france', 52.5, -5, 37.0, 10.5)
DOMAINS['spain'] = Domain('spain', 47.5, -12, 32.0, 3.5)
DOMAINS['italy'] = Domain('italy', 48, 5, 32.5, 20.5)

DEFAULT_DOMAIN = os.environ.get('DOMAIN', 'uk')
