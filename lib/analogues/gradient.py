import numpy as np


def ns(x):
    y = np.roll(x, 1, axis=0)
    y[0, :] = 0
    z = np.roll(x - y, -1, axis=0)
    z[-1, :] = 0
    return z


def sn(x):
    y = np.roll(x, -1, axis=0)
    y[-1, :] = 0
    z = np.roll(y - x, 1, axis=0)
    z[0, :] = 0
    return z


def we(x):
    y = np.roll(x, 1, axis=1)
    y[:, 0] = 0
    z = np.roll(x - y, -1, axis=1)
    z[:, -1] = 0
    return z


def ew(x):
    y = np.roll(x, -1, axis=1)
    y[:, -1] = 0
    z = np.roll(y - x, 1, axis=1)
    z[:, 0] = 0
    return z


if __name__ == '__main__':
    x = np.array([[1, 2, 3, 4], [11, 22, 33, 44], [111, 222, 333, 222], [1, 2, 3, 4], ])
    print(x)

    print('ns')
    print(ns(x))

    print('we')
    print(we(x))

    print('sn')
    print(sn(x))

    print('ew')
    print(ew(x))
