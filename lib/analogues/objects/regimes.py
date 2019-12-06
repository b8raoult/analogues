from .field import Field
import numpy as np
import math
import sys

REGIMES = {}


def adjust(data, minimum, maximum):

    mx = np.amax(data)
    mn = np.amin(data)

    return (data - mn) / (mx - mn) * (maximum - minimum) + minimum


def low():
    data = np.zeros((32, 32))

    center = (16, 16)
    for i in range(0, 32):
        x = i  # + abs(random.random())
        for j in range(0, 32):
            data[i, j] = math.sqrt((x - center[0]) ** 2 + (j - center[1]) ** 2)

    return data


def high():
    data = low()
    m = np.amax(data)
    return m - data


def trough():
    data = np.zeros((32, 32))

    center = (0, 16)
    for i in range(0, 32):
        x = i  # + abs(random.random())
        for j in range(0, 32):
            if x < center[0]:
                x = center[0]
            data[i, j] = math.sqrt((x - center[0]) ** 2 + (j - center[1]) ** 2)

    return data


def ridge():
    data = trough()
    m = np.amax(data)
    return np.flipud(m - data)


class Regime:

    def __init__(self, name, what):
        self.name = name
        self.title = '%03d %s' % (len(REGIMES), name)
        self.what = what

        REGIMES[name] = self

    @classmethod
    def lookup(cls, name):
        return REGIMES[name]

    @property
    def field(self):
        return Field(**self.what)

    @property
    def date(self):
        return self.what.get('date')


class ConstantRegime(Regime):

    @property
    def field(self):

        value = self.what['constant']

        class ConstantField(Field):

            def sample(self, **kargs):
                x = super().sample(**kargs)

                class X:
                    array = np.full(x.array.shape, value, dtype=np.float64)
                    metadata = x.metadata
                    domain = x.domain
                    grid = x.grid
                    date = x.date

                return X()

        return ConstantField(**self.what)


class MatrixRegime(Regime):

    @property
    def field(self):

        value = self.what['field']

        class MatrixField(Field):

            def sample(self, **kargs):
                x = super().sample(**kargs)

                class X:
                    array = np.array(value, dtype=np.float64).reshape(x.array.shape)
                    metadata = x.metadata
                    domain = x.domain
                    grid = x.grid
                    date = x.date

                return X()

        return MatrixField(**self.what)


try:
    ConstantRegime('Heatwave', dict(param='2t', constant=273.15 + 40.11))
    ConstantRegime('Cold spell', dict(param='2t', constant=273.15 - 14.97))

    Regime('Great storm of 1987 (wind gusts)', dict(param='i10fg', date='1987-10-16'))
    Regime('Great storm of 1987 (msl)', dict(param='msl', date='1987-10-16'))
    Regime('Great storm of 1987 (wind speed)', dict(param='ws', date='1987-10-16'))

    ConstantRegime('Clear sky', dict(param='tcc', constant=0))
    ConstantRegime('Overcast', dict(param='tcc', constant=1))

    MatrixRegime('Low pressure (msl)', dict(param='msl', field=adjust(low(), 95000, 100000)))
    MatrixRegime('High pressure (msl)', dict(param='msl', field=adjust(high(), 100000, 102000)))

    ConstantRegime('Dry spell', dict(param='tp', constant=0))
    MatrixRegime('Deluge', dict(param='tp', field=Field('tp').maximum_field))

    # MatrixRegime('Snow everywhere', dict(param='sd', field=Field('sd').maximum_field))
    MatrixRegime('Strong wind', dict(param='ws', field=Field('ws').maximum_field))
    # MatrixRegime('Strong gusts', dict(param='i10fg', field=Field('i10fg').maximum_field))

    ConstantRegime('Anticyclone', dict(param='msl', constant=Field('msl').maximum))
    ConstantRegime('Deep low', dict(param='msl', constant=Field('msl').minimum))

    x = []
    v = 0.001
    for i in range(0, 16):
        row = [0] * 32
        row[i:i + 8] = [v] * 8
        x.append(row)

    for i in range(0, 16):
        x.append(x[15 - i])

    MatrixRegime('Test', dict(param='tp', field=x))

except Exception as e:
    print(e, file=sys.stderr)
