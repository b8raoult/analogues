import numpy as np
import sys

DUMMY = np.zeros((32, 32))


class FieldClim:

    def __init__(self):
        self._minimum_field = None
        self._maximum_field = None
        self._mean_field = None

        self._gradient_ns_max = None
        self._gradient_sn_max = None
        self._gradient_ew_max = None
        self._gradient_we_max = None

        self._gradient_ns_min = None
        self._gradient_sn_min = None
        self._gradient_ew_min = None
        self._gradient_we_min = None

    @property
    def mean_field(self):
        if self._mean_field is None:
            path = self.path('mean')
            try:
                self._mean_field = np.load(path)
            except Exception as e:
                print(e, file=sys.stderr)
                return DUMMY
        return self._mean_field

    @mean_field.setter
    def mean_field(self, mean_field):
        self._mean_field = mean_field
        path = self.path('mean')
        np.save(path, self._mean_field)
        return self._mean_field

    @property
    def maximum_field(self):
        if self._maximum_field is None:
            path = self.path('maximum')
            try:
                self._maximum_field = np.load(path)
            except Exception as e:
                print(e, file=sys.stderr)
                return DUMMY
        return self._maximum_field

    @maximum_field.setter
    def maximum_field(self, maximum_field):
        self._maximum_field = maximum_field
        path = self.path('maximum')
        np.save(path, self._maximum_field)
        return self._maximum_field

    @property
    def minimum_field(self):
        if self._minimum_field is None:
            path = self.path('minimum')
            try:
                self._minimum_field = np.load(path)
            except Exception as e:
                print(e, file=sys.stderr)
                return DUMMY
        return self._minimum_field

    @minimum_field.setter
    def minimum_field(self, minimum_field):
        self._minimum_field = minimum_field
        path = self.path('minimum')
        np.save(path, self._minimum_field)
        return self._minimum_field

    @property
    def gradient_ns_max(self):
        if self._gradient_ns_max is None:
            path = self.path('gradient_ns_max')
            try:
                self._gradient_ns_max = np.load(path)
            except Exception as e:
                print(e, file=sys.stderr)
                return DUMMY
        return self._gradient_ns_max

    @gradient_ns_max.setter
    def gradient_ns_max(self, gradient_ns_max):
        self._gradient_ns_max = gradient_ns_max
        path = self.path('gradient_ns_max')
        np.save(path, self._gradient_ns_max)
        return self._gradient_ns_max

    @property
    def gradient_ns_min(self):
        if self._gradient_ns_min is None:
            path = self.path('gradient_ns_min')
            try:
                self._gradient_ns_min = np.load(path)
            except Exception as e:
                print(e, file=sys.stderr)
                return DUMMY
        return self._gradient_ns_min

    @gradient_ns_min.setter
    def gradient_ns_min(self, gradient_ns_min):
        self._gradient_ns_min = gradient_ns_min
        path = self.path('gradient_ns_min')
        np.save(path, self._gradient_ns_min)
        return self._gradient_ns_min

    @property
    def gradient_sn_max(self):
        if self._gradient_sn_max is None:
            path = self.path('gradient_sn_max')
            try:
                self._gradient_sn_max = np.load(path)
            except Exception as e:
                print(e, file=sys.stderr)
                return DUMMY
        return self._gradient_sn_max

    @gradient_sn_max.setter
    def gradient_sn_max(self, gradient_sn_max):
        self._gradient_sn_max = gradient_sn_max
        path = self.path('gradient_sn_max')
        np.save(path, self._gradient_sn_max)
        return self._gradient_sn_max

    @property
    def gradient_sn_min(self):
        if self._gradient_sn_min is None:
            path = self.path('gradient_sn_min')
            try:
                self._gradient_sn_min = np.load(path)
            except Exception as e:
                print(e, file=sys.stderr)
                return DUMMY
        return self._gradient_sn_min

    @gradient_sn_min.setter
    def gradient_sn_min(self, gradient_sn_min):
        self._gradient_sn_min = gradient_sn_min
        path = self.path('gradient_sn_min')
        np.save(path, self._gradient_sn_min)
        return self._gradient_sn_min

    @property
    def gradient_we_max(self):
        if self._gradient_we_max is None:
            path = self.path('gradient_we_max')
            try:
                self._gradient_we_max = np.load(path)
            except Exception as e:
                print(e, file=sys.stderr)
                return DUMMY
        return self._gradient_we_max

    @gradient_we_max.setter
    def gradient_we_max(self, gradient_we_max):
        self._gradient_we_max = gradient_we_max
        path = self.path('gradient_we_max')
        np.save(path, self._gradient_we_max)
        return self._gradient_we_max

    @property
    def gradient_we_min(self):
        if self._gradient_we_min is None:
            path = self.path('gradient_we_min')
            try:
                self._gradient_we_min = np.load(path)
            except Exception as e:
                print(e, file=sys.stderr)
                return DUMMY
        return self._gradient_we_min

    @gradient_we_min.setter
    def gradient_we_min(self, gradient_we_min):
        self._gradient_we_min = gradient_we_min
        path = self.path('gradient_we_min')
        np.save(path, self._gradient_we_min)
        return self._gradient_we_min

    @property
    def gradient_ew_max(self):
        if self._gradient_ew_max is None:
            path = self.path('gradient_ew_max')
            try:
                self._gradient_ew_max = np.load(path)
            except Exception as e:
                print(e, file=sys.stderr)
                return DUMMY
        return self._gradient_ew_max

    @gradient_ew_max.setter
    def gradient_ew_max(self, gradient_ew_max):
        self._gradient_ew_max = gradient_ew_max
        path = self.path('gradient_ew_max')
        np.save(path, self._gradient_ew_max)
        return self._gradient_ew_max

    @property
    def gradient_ew_min(self):
        if self._gradient_ew_min is None:
            path = self.path('gradient_ew_min')
            try:
                self._gradient_ew_min = np.load(path)
            except Exception as e:
                print(e, file=sys.stderr)
                return DUMMY
        return self._gradient_ew_min

    @gradient_ew_min.setter
    def gradient_ew_min(self, gradient_ew_min):
        self._gradient_ew_min = gradient_ew_min
        path = self.path('gradient_ew_min')
        np.save(path, self._gradient_ew_min)
        return self._gradient_ew_min
