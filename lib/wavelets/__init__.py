# import scipy.misc
# import matplotlib.pyplot as plt
import pywt
import numpy as np
import math


# [cA3, (cH3, cV3, cD3), (cH2, cV2, cD2), (cH1, cV1, cD1)]

# -----------------------------------------------------------------
# |  cA3  |  cH3  |               |                               |
# | (1x1) | (1x1) |      cH2      |                               |
# -----------------     (2x2)     |                               |
# |  cV3  |  cD3  |               |                               |
# | (1x1) | (1x1) |               |              cH1              |
# ---------------------------------             (4x4)             |
# |               |               |                               |
# |      cV2      |      cD2      |                               |
# |     (2x2)     |     (2x2)     |                               |
# |               |               |                               |
# |               |               |                               |
# -----------------------------------------------------------------
# |                               |                               |
# |                               |                               |
# |                               |                               |
# |                               |                               |
# |              cV1              |              cD1              |
# |             (4x4)             |             (4x4)             |
# |                               |                               |
# |                               |                               |
# |                               |                               |
# |                               |                               |
# |                               |                               |
# -----------------------------------------------------------------

def all_wavelets():
    for family in pywt.families():
        for n in pywt.wavelist(family):
            if n == 'db1':  # Same as Haar
                continue
            yield n


class Wavelet2D(object):

    def __init__(self, data, wavelet='haar', mode='sym', level=5):

        self.wavelet = wavelet
        self.mode = mode
        self.level = level
        self.data = data

        self._signature = None
        self._coeff = None

        self._flat_coeff = None


    @property
    def size(self):
        return len(self.coeff)

    @property
    def coeff(self):
        if self._coeff is None:
            self._coeff = pywt.wavedec2(self.data, self.wavelet, level=self.level, mode=self.mode)
        return self._coeff

    @property
    def flat_coeff(self):
        if self._flat_coeff is None:
            flat = []

            approx = self.coeff[0]
            flat.append(approx.flat)
            details = self.coeff[1:]
            for horizontal, vertical, diagonal in details:
                flat.append(horizontal.flat)
                flat.append(vertical.flat)
                flat.append(diagonal.flat)

            self._flat_coeff = [item for sublist in flat for item in sublist]
        return self._flat_coeff

    def visit_coeff(self, visitor):
        approx = self.coeff[0]
        visitor(approx, 0)

        details = self.coeff[1:]
        n = 1
        for horizontal, vertical, diagonal in details:
            visitor(horizontal, n)
            visitor(vertical, n)
            visitor(diagonal, n)
            n += 1

    @property
    def signature(self):
        if self._signature is None:
            approx = self.coeff[0]
            result = [approx.shape]
            details = self.coeff[1:]
            for horizontal, vertical, diagonal in details:
                result.append((horizontal.shape, vertical.shape, diagonal.shape))
            self._signature = result
        return self._signature

    def graymap(self):

        approx = self.coeff[0]
        width, height = approx.shape
        details = self.coeff[1:]

        width += 1
        height += 1

        for horizontal, vertical, diagonal in details:
            w, h = horizontal.shape
            width += w + 2
            height += h + 2

        result = np.empty((width, height), approx.dtype)
        result.fill(0)

        w, h = approx.shape

        mn = np.min(approx)
        mx = np.max(approx)
        if mn == mx:
            mx = approx
            mn = 0

        a = 0
        result[a:a+w, a:a+h] = (approx - mn) / ( mx - mn) * 255

        pw = w
        ph = h

        for horizontal, vertical, diagonal in details:
            w, h = horizontal.shape

            mnh = np.min(horizontal)
            mnv = np.min(vertical)
            mnd = np.min(diagonal)
            mxh = np.max(horizontal)
            mxv = np.max(vertical)
            mxd = np.max(diagonal)
            mn = min([mnh, mnv, mnd])
            mx = max([mxh, mxv, mxd])
            if mn == mx:
                mx = approx
                mn = 0
            result[a+pw:a+pw + w, a:a+h] = (horizontal - mn) / ( mx - mn) * 255
            result[a:a+w, a+ph:a+ph + h] = (vertical  - mn) / ( mx - mn) * 255
            result[a+pw:a+pw + w, a+ph:a+ph + h] = (diagonal  - mn) / ( mx - mn) * 255

            pw += w + 1
            ph += h + 1
            a += 1

        return result

    def non_zeros(self):

        approx = self.coeff[0]
        width, height = approx.shape
        details = self.coeff[1:]

        n = 0
        result = 0
        for horizontal, vertical, diagonal in details:
            if np.count_nonzero(horizontal) + np.count_nonzero(vertical) + np.count_nonzero(diagonal):
                result = n
            n += 1
        return result

    def unstructured(self):

        approx = self.coeff[0]
        width, height = approx.shape
        details = self.coeff[1:]

        for horizontal, vertical, diagonal in details:
            w, h = horizontal.shape
            width += w
            height += h

        result = np.empty((width, height), approx.dtype)

        w, h = approx.shape

        result[0:w, 0:h] = approx

        pw = w
        ph = h

        for horizontal, vertical, diagonal in details:
            w, h = horizontal.shape

            result[pw:pw + w, 0:h] = horizontal
            result[0:w, ph:ph + h] = vertical
            result[pw:pw + w, ph:ph + h] = diagonal

            pw += w
            ph += h

        return result

    def structured(self, array):

        w, h = array.shape

        sig = self.signature

        approx = sig[0]
        details = sig[1:]

        pw, ph = approx

        result = [array[0:pw, 0:ph]]

        for (w, h), _, _ in details:
            horizontal = array[pw:pw + w, 0:h]
            vertical = array[0:w, ph:ph + h]
            diagonal = array[pw:pw + w, ph:ph + h]
            result.append((horizontal, vertical, diagonal))

            pw += w
            ph += h

        return Wavelet2D(pywt.waverec2(result, self.wavelet, mode=self.mode))

    def energy(self):

        result = 0

        def add(g):
            f = g.flat
            return sum([x * x for x in f])  # / len(f)

        approx = self.coeff[0]
        result += add(approx)
        details = self.coeff[1:]
        for horizontal, vertical, diagonal in details:
            result += add(horizontal)
            result += add(vertical)
            result += add(diagonal)

        return result

    def clear(self, n):
        c = self.coeff
        for _ in range(0, n):
            c.pop()
        self._coeff = None
        return Wavelet2D(pywt.waverec2(c, self.wavelet))

    def zero(self, n):
        c = self.coeff
        for i in range(0, n):
            k = -(i + 1)
            try:
                shape = c[k][0].shape
            except:
                print ("zero failed k=", k, "n=", n)
                print ("c=", len(c))
                raise
            c[k] = (np.zeros(shape), np.zeros(shape), np.zeros(shape))
        self._coeff = None
        return Wavelet2D(pywt.waverec2(c, self.wavelet, mode=self.mode))

    def keep(self, n):
        m = sorted([math.fabs(x) for x in self.flat_coeff], reverse=True)[n - 1]
        return self.hard_threshold(m)

    def hard_threshold(self, t):
        u = self.unstructured()
        u[np.absolute(u) < t] = 0
        return self.structured(u)
