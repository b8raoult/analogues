from __future__ import absolute_import


from scipy.stats.stats import pearsonr
from scipy.spatial.distance import cosine
import numpy as np

try:
    from . import wemd, emd, hilbert
    WEMD = wemd.wemd
    EMD = emd.emd
    HILBERT = hilbert.distance
except:
    pass


def L1(a, b):
    return sum(np.absolute((a-b).flat))


def L2(a, b):
    return np.linalg.norm((a-b).flat)


def PCC(a, b):
    return 1 - pearsonr(a.flat, b.flat)[0]


MANHATTAN = L1
RMS = L2

def COSINE(a, b):
    return cosine(a.flat, b.flat)


# if __name__ == "__main__":
#     print PCC(np.array([1, 2, 3]), np.array([4, 5, 6]))

