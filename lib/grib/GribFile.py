from grib_bindings import bindings as grib

import os
from grib import GribField


class GribFile(object):

    def __init__(self, path):

        if path.startswith('~'):
            path = os.path.expanduser(path)

        # print("GribFile", path)
        self.path = path
        self.f = grib.grib_file_open(path)

    def __del__(self):
        try:
            self.f.close()
        except:
            pass

    def __iter__(self):
        return self

    def __next__(self):
        field = self.f.next()
        if not field:
            raise StopIteration()
        return GribField.GribField(self.path, field)

    next = __next__

    def at_offset(self, offset):
        # print("GribFile at_offset", offset)
        self.f.position(offset)
        return self.__next__()
