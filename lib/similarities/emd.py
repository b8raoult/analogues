#!/usr/local/bin/python

import numpy as np
import math
import pyemd
import os


CACHE = {}


def iter(ni, nj):
    for i in range(0, ni):
        for j in range(0, nj):
            yield (i, j, j + i * nj)


def distances(ni, nj, dist_max):

    key = (ni, nj, dist_max)
    if key in CACHE:
        return CACHE[key]

    cache = "emd-ground_distance-%d-%d-%d.cache" % key
    if os.path.exists(cache):
        print "Load", cache
        with open(cache) as f:
            ground_distance = np.load(f)

    else:
        print "Create", cache
        ground_distance = np.zeros((ni*nj, ni*nj))
        for i in iter(ni, nj):
            for j in iter(ni, nj):
                dx = i[0] - j[0]
                dy = i[1] - j[1]
                d = math.sqrt(dx * dx + dy * dy)
                if d > dist_max:
                    d = dist_max
                ground_distance[i[2], j[2]] = d


        with open(cache, "w") as f:
            ground_distance.dump(f)

    print "Done"
    CACHE[key] = ground_distance
    return ground_distance


def emd(a, b, dist_max=2):
    ni, nj = a.shape
    return pyemd.emd(a.flatten(), b.flatten(), distances(ni, nj, dist_max))

