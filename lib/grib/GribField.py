from __future__ import absolute_import
from grib_bindings import bindings as grib
import numpy as np
import datetime

SCALE = {'10si': (1, 0),
         '2t': (1, -273.15),
         # 'tp': (1000, 0),
         'tp': (1, 0),
         'logtp': (1, 0),
         'sp': (0.01, 0)}
# OFFSET = {'2t': -273.15, '10'}


class SubField(object):

    def __init__(self, owner, area):
        self.owner = owner
        self._array = None
        self.area = area
        self.grid = owner.grid

    @property
    def array(self):
        if self._array is None:
            nj, ni = self.Nj, self.Ni
            oj, oi = self.owner.Nj, self.owner.Ni

            tn, tw, ts, te = self.area
            on, ow, os, oe = self.owner.area

            we, ns = self.grid

            while tw > oe:
                tw -= 360
                te -= 360

            while te < ow:
                tw += 360
                te += 360

            while te > 360:
                tw -= 360
                te -= 360

            # print tw, te

            # print ow, oe

            start_j = int((on - tn) / ns)
            start_i = int((tw - ow) / we)

            # print 'start j', start_j
            # print 'start i', start_i, ni, nj

            if start_j < 0:
                raise Exception("Oops")

            b = self.owner.array

            if start_i < 0:
                if -start_i >= ni:
                    raise Exception("Oops")
                else:
                    a = np.empty((nj, ni))
                    # a = np.zeros((nj, ni))

                    delta = ni + start_i
                    # print delta

                    a[0:nj, -delta:ni] = b[start_j:start_j + nj, 0:delta]
                    a[0:nj, 0:-start_i] = b[start_j:start_j + nj, start_i:oi]
            else:
                a = b[start_j:start_j + nj, start_i:start_i + ni]
            self._array = a

        return self._array

    @property
    def scaled_array(self):
        s, o = SCALE[self.owner.shortName]
        return self.array * s + o

    @property
    def first_latitude(self):
        return self.area[0]

    @property
    def latitude_increment(self):
        return self.owner.latitude_increment

    @property
    def first_longitude(self):
        return self.area[1]

    @property
    def longitude_increment(self):
        return self.owner.longitude_increment

    @property
    def Nj(self):
        n, w, s, e = self.area
        we, ns = self.grid
        return int((n - s) / ns + 1)

    @property
    def Ni(self):
        n, w, s, e = self.area
        we, ns = self.grid
        while e < w:
            e += 360
        return int((e - w) / we + 1)

    @property
    def metadata(self):
        return self.owner.metadata


class GribField:

    def __init__(self, path, handle):
        self.path = path
        self.handle = handle
        self._array = None
        self._meshgrid = None

    def __del__(self):
        if self.handle:
            grib.grib_handle_delete(self.handle)

    @property
    def array(self):
        if self._array is None:
            grib.grib_set(self.handle, "missingValue", 0.0)
            self._array = grib.grib_get_double_array(self.handle, "values").reshape((self.Nj, self.Ni))
        return self._array

    def __getattr__(self, name):
        # print("GRIB GET", name)
        return grib.grib_get(self.handle, name)

    @property
    def class_(self):
        return self.__getattr__('class')

    def __getitem__(self, name):
        print("GRIB GET", name)
        return grib.grib_get(self.handle, name)

    def set(self, name, value):
        grib.grib_set(self.handle, name, value)

    def write(self, path, mode='w'):
        grib.grib_write_message(self.handle, path, mode)

    @property
    def area(self):
        return (self.latitudeOfFirstGridPointInDegrees,
                self.longitudeOfFirstGridPointInDegrees,
                self.latitudeOfLastGridPointInDegrees,
                self.longitudeOfLastGridPointInDegrees)

    @property
    def grid(self):
        # i = w-e, j = n-s
        return (self.iDirectionIncrementInDegrees, self.jDirectionIncrementInDegrees)

    @property
    def meshgrid(self):
        if self._meshgrid is None:
            # TODO: Use iterator

            north, west, south, east = self.area

            x = np.linspace(west, east, self.Ni)
            y = np.linspace(north, south, self.Nj)

            self._meshgrid = np.meshgrid(x, y)

        return self._meshgrid

    @property
    def first_latitude(self):
        return self.latitudeOfFirstGridPointInDegrees

    @property
    def latitude_increment(self):
        return -self.jDirectionIncrementInDegrees

    @property
    def first_longitude(self):
        return self.longitudeOfFirstGridPointInDegrees

    @property
    def longitude_increment(self):
        return self.iDirectionIncrementInDegrees

    def subarea(self, area):
        return SubField(self, area)

    @property
    def valid_date(self):
        step = self.step
        return self.base_date + datetime.timedelta(hours=step)

    @property
    def base_date(self):
        date, time = self.date, self.time
        # print(date, time, date // 10000, (date % 10000) // 100, date % 100, time // 100, time % 100, 0)

        return datetime.datetime(date // 10000, (date % 10000) // 100, date % 100, time // 100, time % 100, 0)

    @property
    def metadata(self):

        # See Magics's WebLibrary::askId(MetaDataCollector& request)

        return {
                "paramId": str(grib.grib_get(self.handle, "paramId")),
                "units": grib.grib_get(self.handle, "units"),
                "type": grib.grib_get(self.handle, "type"),
                "typeOfLevel": grib.grib_get(self.handle, "typeOfLevel"),
                "area": self.area,
                "grid": self.grid,
                # "level": "0",
                "shortName": grib.grib_get(self.handle, "shortName"),
                # "long_name": grib.grib_get(self.handle, "long_name"),
                # "param": grib.grib_get(self.handle, "param"),
                # "marsClass": "od",
                # "marsStream": "enfo",
                # "marsType": "pf",
                # "number": "50",
                # "paramId": "228",
                # "shortName": "tp",
                # "stepRange": "24",
                # "typeOfLevel": "surface",
                # "units": grib.grib_get(self.handle, "units"),
                # "stepRange": grib.grib_get(self.handle, "stepRange"),

                "levelist": grib.grib_get(self.handle, "level"),
                "level": grib.grib_get(self.handle, "level")
                }

    def subfields(self, size=(32, 32), increment=(1, 1), south=-90, north=90):
        n, w, s, e = self.area
        we, ns = self.grid
        for j in range(0, self.Nj, increment[1]):
            for i in range(0, self.Ni, increment[0]):
                area = (n - j * ns,
                        w + i * we,
                        n - (j + size[1] - 1) * ns,
                        w + (i + size[0] - 1) * we,)
                # print area
                if area[2] >= south and area[0] <= north:
                    yield self.subarea(area)

    def set_array(self, array):
        self._array = array
