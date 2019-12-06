#!/usr/local/bin/python

import numpy as np
import math
import pywt


def wemd(a, b, type='db8'):
    w = 0
    array = a - b

    avg = np.mean(array.flat)
    # avg = 0

    ndims = 2
    coeffs = pywt.wavedec2(array - avg, type)
    # print coeffs
    # w += sum(np.absolute(coeffs[0].flat))
    J = len(coeffs)
    for i in range(1, J):
        # j = J - i - 1
        j = i - 1

        p = math.pow(2, -j * (1.0 + ndims / 2.0))
        # print 'j=', j, 'p=', p, max(h.flat), max(v.flat),
        s = 0

        h, v, d = coeffs[i]
        # print sum(np.absolute(h.flat)) * p, sum(np.absolute(v.flat)) * p, sum(np.absolute(d.flat)) * p
        s += sum(np.absolute(h.flat))
        s += sum(np.absolute(v.flat))
        s += sum(np.absolute(d.flat))

        w += s * p

    return w + avg

if __name__ == "__main__":
    # n = 64
    # a = np.array([range(0, n)] * n, np.float64)
    # b = np.array([list(reversed(range(0, n)))] * n, np.float64)
    a = np.zeros((200, 200), np.float64)

    b = np.ones((200, 200), np.float64) * 10000

    print wemd(a, b)

    # a = np.ones((4, 4), np.float64)

    # b = np.array([[0, 0, 0, 0],
    #               [0, 0, 0, 0],
    #               [0, 0, 0, 0],
    #               [0, 0, 0, 1]], np.float64)

    # print a.shape, b.shape
    # print wemd(a, b)
    # import emd
    # print emd.emd(a, b, 9999)

    # a = np.array([[1, 3, 0],
    #               [0, 0, 0],
    #               [0, 0, 0]], np.float64)

    # b = np.array([[0, 0, 0],
    #               [0, 0, 0],
    #               [0, 0, 1]], np.float64)

    # print a.shape, b.shape
    # print wemd(a, b)
    # import emd
    # print emd.emd(a, b, 9999)

    # a = np.array([[1, 3, 0],
    #               [0, 0, 0],
    #               [0, 0, 0]], np.float64)

    # b = np.array([[0, 3, 0],
    #               [1, 0, 0],
    #               [-2, 0, 1]], np.float64)

    # print a.shape, b.shape
    # print wemd(a, b)
    # import emd
    # print emd.emd(a, b, 9999)

    # n = 64
    # a = np.array([range(0, n)] * n, np.float64)
    # b = np.array([list(reversed(range(0, n)))] * n, np.float64)
    # print a.shape, b.shape
    # print wemd(a, b)
    # import emd
    # print emd.emd(a, b, 5)
