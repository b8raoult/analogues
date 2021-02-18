# import scipy.misc
# import matplotlib.pyplot as plt
import pywt
import numpy as np


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


