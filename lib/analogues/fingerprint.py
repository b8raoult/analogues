import bitstring
from wavelets import Wavelet2D
import numpy as np
import pywt
from similarities import L2
import pickle
import math
HAAR = pywt.Wavelet('haar')


class ZeroCompressor(object):

    def compress(self, wavelet, depth):
        return wavelet.zero(depth)

    def width(self, fingerprint):
        # print(fingerprint.depth)
        # print(len(fingerprint.wavelet.coeff))
        # print(fingerprint.wavelet.coeff[fingerprint.depth][0].shape)
        return fingerprint.wavelet.coeff[fingerprint.depth + 1][0].shape


class KeepCompressor(object):
    """
    Perform hard thresold on the wavelets
    and keep the N most important values
    """

    def compress(self, wavelet, depth):
        keep = (5 - depth) * 4
        return wavelet.keep(keep)

    def width(self, fingerprint):
        """
        If  keep=2, we have three values: 0, and 2 above zero
        """
        # n = fingerprint.compress_wavelet.non_zeros()
        # return fingerprint.wavelet.coeff[n + 1][0].shape
        return 1, 1


class FingerPrinter1bit(object):

    def distance(self, a, b):
        # Hamming distance
        return (np.count_nonzero(a.bits ^ b.bits), abs(a.value - b.value))

    def infinity(self, fingerprint):
        return (float('inf'), float('inf'))

    def bits(self, fingerprint):
        t = fingerprint.fingerprint
        w1, h1 = fingerprint.width
        t = t[0::w1, 0::h1]
        return t
        # return bitstring.ConstBitArray(t.flat)

    # def encode(self, fingerprint):
    #     return "0x%s %g" % (fingerprint.bits.hex, fingerprint.value)

    def bitstring(self, fingerprint):
        return bitstring.ConstBitArray(fingerprint.bits.flat)

    def encode(self, fingerprint):
        return pickle.dumps((fingerprint.bits, fingerprint.value))

    def decode(self, data):
        return pickle.loads(data)

    def to_db(self, fingerprint, d):
        d['fingerprint_s'] = int(''.join(['1' if x else '0' for x in fingerprint.bits.flat]), 2)
        d['fingerprint_r'] = fingerprint.value
        d['field_min'] = fingerprint.field_min
        d['field_max'] = fingerprint.field_max

    def as_json(self, fingerprint):
        return {"bits": [1 if x else 0 for x in fingerprint.bits.flat], "value": float(fingerprint.value)}


class FingerPrinterMean(FingerPrinter1bit):

    def fingerprint(self, data):
        z = np.copy(data)
        p = np.mean(z)
        t = np.copy(z)
        # t[np.absolute(z) >= p] = 1
        # t[np.absolute(z) < p] = 0
        t[z > p] = 1
        t[z <= p] = 0

        # # TMP fix, should change the >= above to >
        # if np.sum(t) == t.size:
        #     t = t * 0

        return t.astype(dtype='bool')

    def representation(self, fingerprint):
        b = bitstring.ConstBitArray(fingerprint.bits.flat)
        return "mean(%s,%s)" % (b.hex, fingerprint.value)


class FingerPrinterMedian(FingerPrinter1bit):

    def fingerprint(self, data):
        z = np.copy(data)
        p = np.median(z)
        t = np.copy(z)
        # t[np.absolute(z) >= p] = 1
        # t[np.absolute(z) < p] = 0
        t[z > p] = 1
        t[z <= p] = 0

        # # TMP fix, should change the >= above to >
        # if np.sum(t) == t.size:
        #     t = t * 0

        return t.astype(dtype='bool')

    def representation(self, fingerprint):
        b = bitstring.ConstBitArray(fingerprint.bits.flat)
        return "median(%s,%s)" % (b.hex, fingerprint.value)


class MixinZ(object):

    def infinity(self, fingerprint):
        return float('inf')

    def distance(self, a, b):
        # Hamming distance
        x = a.options[0]
        m = max(abs(a.value), abs(b.value))
        p = np.count_nonzero(a.bits ^ b.bits) / float(a.bits.size)
        if m == 0:
            return p
        return x * abs(a.value - b.value) / m + p

    def distance_with_mask(self, a, b, mask):
        n = b.value / 6.0
        if n == 0:
            n = 1

        x = a.options[0]

        m = max(abs(a.value), abs(b.value / n))
        p = np.count_nonzero((a.bits | mask) ^ (b.bits | mask)) / float(a.bits.size)
        if m == 0:
            return p
        return x * abs(a.value - b.value / n) / m + p

    def make_mask(self, a, mask):
        # raise Exception(mask)
        size = a.bits.shape
        result = np.empty(size, 'bool')
        di = mask.shape[0] / size[0]
        dj = mask.shape[1] / size[1]
        for i in range(0, size[0]):
            for j in range(0, size[1]):
                result[i, j] = not np.any(mask[i * di:(i + 1) * di, j * dj:(j + 1) * dj])

        return result


class MixinW(object):

    def infinity(self, fingerprint):
        return float('inf')

    def distance(self, a, b):
        # Hamming distance
        x = a.options[0]
        h = np.count_nonzero(a.bits ^ b.bits)
        return x * abs(a.value - b.value) + h

    def distance_with_mask(self, a, b, mask):
        assert False
        n = b.value / 6.0
        if n == 0:
            n = 1

        x = a.options[0]

        m = max(abs(a.value), abs(b.value / n))
        p = np.count_nonzero((a.bits | mask) ^ (b.bits | mask)) / float(a.bits.size)
        if m == 0:
            return p
        return x * abs(a.value - b.value / n) / m + p

    def make_mask(self, a, mask):
        # raise Exception(mask)
        size = a.bits.shape
        result = np.empty(size, 'bool')
        di = mask.shape[0] / size[0]
        dj = mask.shape[1] / size[1]
        for i in range(0, size[0]):
            for j in range(0, size[1]):
                result[i, j] = not np.any(mask[i * di:(i + 1) * di, j * dj:(j + 1) * dj])

        return result


class FingerPrinterMedianZ(MixinZ, FingerPrinterMedian):
    pass


class FingerPrinterMeanZ(MixinZ, FingerPrinterMean):
    pass


class FingerPrinterMeanW(MixinW, FingerPrinterMean):
    pass


class FingerPrinterMeanY(FingerPrinterMean):

    def infinity(self, fingerprint):
        return float('inf')

    def distance(self, a, b):
        s = a.options[2]
        va = self.scaled_value(a)
        vb = self.scaled_value(b)
        d = abs(va - vb) / 65535.0
        h = np.count_nonzero(a.bits ^ b.bits) / float(a.bits.size)
        return h + d * s

    def scaled_value(self, fingerprint):
        o = fingerprint.options
        v = int((fingerprint.value - o[0]) / (o[1] - o[0]) * 65535)
        if v < 0:
            v = 0
        if v > 65535:
            v = 65535
        return v

    def encode(self, fingerprint):
        return pickle.dumps((fingerprint.bits, fingerprint.value))

    def representation(self, fingerprint):
        b = bitstring.ConstBitArray(fingerprint.bits.flat)
        return "meany(%s,%s)" % (b.hex, hex(self.scaled_value(fingerprint)))


class FingerPrinterFull(object):

    def infinity(self, fingerprint):
        return float('inf')

    def distance(self, a, b):
        # print('distance', a.bits, b.bits, L2(a.bits, b.bits))
        return L2(a.bits, b.bits)

    def fingerprint(self, data):
        return data

    def packed(self, fingerprint):
        # return fingerprint.fingerprint
        t = fingerprint.fingerprint
        w1, h1 = fingerprint.width
        t = t[0::w1, 0::h1]
        return t

    def bits(self, fingerprint):
        return self.packed(fingerprint)

    def encode(self, fingerprint):
        return pickle.dumps(fingerprint.bits)

    def decode(self, data):
        return (pickle.loads(data), 0)

    def representation(self, fingerprint):
        return "full(%s)" % (fingerprint.bits.flatten())


class FingerPrinter2bits(object):

    def fingerprint(self, data):
        p = [np.percentile(data, x) for x in [0, 25, 50, 75, 100]]

        n = 0
        t = np.copy(data)
        z = np.copy(data)

        for a, b in zip(p[:-1], p[1:]):
            t[(z >= a) & (z <= b)] = n
            n = n + 1
            # print t

        return t.astype(dtype='int')

    def infinity(self, fingerprint):
        return (float('inf'), float('inf'))

    def compress(self, wavelet, depth):
        return wavelet.zero(depth)

    def packed(self, fingerprint):
        t = fingerprint.fingerprint
        w1, h1 = fingerprint.width
        return t[0::w1, 0::h1]

    def bits(self, fingerprint):
        return self.packed(fingerprint)

    def encode(self, fingerprint):
        return pickle.dumps((fingerprint.bits, fingerprint.value))

    def decode(self, data):
        return pickle.loads(data.decode())

    def distance(self, a, b):
        return (L2(a.bits, b.bits), abs(a.value - b.value))

    def representation(self, fingerprint):
        t = fingerprint.bits
        b = bitstring.ConstBitArray().join(bitstring.BitArray(uint=x, length=2) for x in t.flat)
        return "2bits(%s,%s)" % (b, fingerprint.value)


class FingerPrinter2bitsZ(FingerPrinter2bits):

    def infinity(self, fingerprint):
        return float('inf')

    def distance(self, a, b):
        return abs(a.value - b.value) / max(abs(a.value), abs(b.value)) + L2(a.bits, b.bits)


HANDLERS = {
    'median': (FingerPrinterMedian, ZeroCompressor),
    'mean': (FingerPrinterMean, ZeroCompressor),
    'full': (FingerPrinterFull, ZeroCompressor),
    '2bits': (FingerPrinter2bits, ZeroCompressor),
    'medianx': (FingerPrinterMedian, KeepCompressor),
    'meanx': (FingerPrinterMean, KeepCompressor),
    'fullx': (FingerPrinterFull, KeepCompressor),
    '2bitsx': (FingerPrinter2bits, KeepCompressor),
    'medianz': (FingerPrinterMedianZ, ZeroCompressor),
    'meanz': (FingerPrinterMeanZ, ZeroCompressor),
    'meany': (FingerPrinterMeanY, ZeroCompressor),
    'meanw': (FingerPrinterMeanW, ZeroCompressor),
    '2bitsz': (FingerPrinter2bitsZ, ZeroCompressor)}


def handler(mode):
    options = mode.split('_')
    h, c = HANDLERS[options[0]]
    return tuple([h(), c(), [float(x) for x in options[1:]]])


class FingerPrintBase(object):

    def __init__(self, mode):
        h, c, o = handler(mode)
        self.handler = h
        self.compressor = c
        self.options = o

    def as_json(self):
        return self.handler.as_json(self)

    def infinity(self):
        return self.handler.infinity(self)

    def make_mask(self, mask):
        return self.handler.make_mask(self, mask)

    def distance(self, other):
        return self.handler.distance(self, other)

    def distance_with_mask(self, other, mask):
        return self.handler.distance_with_mask(self, other, mask)

    @property
    def width(self):
        return self.compressor.width(self)

    def __repr__(self):
        return self.handler.representation(self)


class FingerPrintFromDB(FingerPrintBase):

    def __init__(self, bits, mode):
        super(FingerPrintFromDB, self).__init__(mode)
        self.bits, self.value = self.handler.decode(bits)


class FingerPrint(FingerPrintBase):

    def __init__(self, data, depth, wavelet='haar', mode='meanw_1'):
        super(FingerPrint, self).__init__(mode)

        level = pywt.dwt_max_level(len(data), HAAR)
        self.wavelet = Wavelet2D(data, wavelet=wavelet, level=level)
        self.depth = depth

        assert depth >= 0
        self._fingerprint = None
        self._compressed_wavelet = None
        self._bits = None

        self.field_min = np.amin(data)
        self.field_max = np.amax(data)

    @property
    def compress_wavelet(self):
        if self._compressed_wavelet is None:
            self._compressed_wavelet = self.compressor.compress(self.wavelet, self.depth)
        return self._compressed_wavelet

    @property
    def fingerprint(self):
        if self._fingerprint is None:
            self._fingerprint = self.handler.fingerprint(self.compress_wavelet.data)
        return self._fingerprint

    @property
    def fingerprint_packed(self):
        return self.handler.packed(self)

    @property
    def bits(self):
        if self._bits is None:
            self._bits = self.handler.bits(self)
        return self._bits

    def encode(self):
        return self.handler.encode(self)

    def to_db(self, d):
        return self.handler.to_db(self, d)

    @property
    def value(self):
        # This should return the value
        return (self.wavelet.coeff[0][0] / self.wavelet.data.shape[0])[0]

    @property
    def bitstring(self):
        return self.handler.bitstring(self)
