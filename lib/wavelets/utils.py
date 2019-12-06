# import scipy.misc
# import matplotlib.pyplot as plt
import pywt
import numpy as np


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

def Wavelet(object):

    def __init__(self, data, wavelet='haar', mode='sym', level=None):
        self.wavelet = wavelet
        self.mode = mode
        self.level = level
        self.data = data
        self.coeff = pywt.wavedec2(data, self.wavelet, level=self.level)

    def signature(self):
        approx = self.coeff[0]
        result = [approx.shape]
        details = self.coeff[1:]
        for horizontal, vertical, diagonal in details:
            result.append((horizontal.shape, vertical.shape, diagonal.shape))
        return result

    # def equal(self, coeff1, coeff2):
    #     assert np.array_equal(coeff1[0], coeff2[0])
    #     details1 = coeff1[1:]
    #     details2 = coeff2[1:]
    #     assert len(details1) == len(details2)
    #     for (h1, v1, d1), (h2, v2, d2) in zip(details1, details2):
    #         assert np.array_equal(h1[0], h2[0])
    #         assert np.array_equal(v1[0], v2[0])
    #         assert np.array_equal(d1[0], d2[0])

    def unstructured(self, scale=False):

        approx = self.coeff[0]
        width, height = approx.shape
        details = self.coeff[1:]

        for horizontal, vertical, diagonal in details:
            w, h = horizontal.shape
            width += w
            height += h

        result = np.empty((width, height), approx.dtype)

        w, h = approx.shape

        s = 1.0 / len(self.coeff)
        if scale:
            result[0:w, 0:h] = approx * s
            print s, max(approx.flat), s * max(approx.flat)
        else:
            result[0:w, 0:h] = approx

        pw = w
        ph = h

        s *= 2

        for horizontal, vertical, diagonal in details:
            w, h = horizontal.shape

            if scale:
                result[pw:pw + w, 0:h] = horizontal * s
                result[0:w, ph:ph + h] = vertical * s
                result[pw:pw + w, ph:ph + h] = diagonal * s
                print s, max(horizontal.flat), s * max(horizontal.flat)
            else:
                result[pw:pw + w, 0:h] = horizontal
                result[0:w, ph:ph + h] = vertical
                result[pw:pw + w, ph:ph + h] = diagonal

            pw += w
            ph += h

            s *= 2

        return result

    def structured(self, array, signature):

        w, h = array.shape

        approx = signature[0]
        details = signature[1:]

        pw, ph = approx

        result = [array[0:pw, 0:ph]]

        for (w, h), _, _ in details:
            horizontal = array[pw:pw + w, 0:h]
            vertical = array[0:w, ph:ph + h]
            diagonal = array[pw:pw + w, ph:ph + h]
            result.append((horizontal, vertical, diagonal))

            pw += w
            ph += h

        return result


