import os
import sys
sys.path.append("/usr/local/apps/grib_api/1.15.0/GNU/4.8.1/lib/python2.7/site-packages/gribapi")
sys.path.append("/usr/local/apps/python/2.7.8-01/lib/python2.7/site-packages")

try:
    import ecmwfapi
except:
    pass

import numpy as np
import tempfile

try:
    from grib import GribFile
except:
    pass

ANALOGUES_HOME = os.environ.get("ANALOGUES_HOME", os.path.expanduser("~/Dropbox/phd"))
ANALOGUES_CACHE = os.environ.get("ANALOGUES_CACHE", os.path.expanduser("/tmp"))
ANALOGUES_FILES = os.environ.get("ANALOGUES_FILES", os.path.expanduser("/tmp"))

# MODE = {('2t', 3): 'meanz_19.03',
#         ('msl', 3): 'meanz_32.18',
#         ('sd', 3): 'meanz_0.13',
#         ('sp', 3): 'meanz_19.8',
#         ('tp', 3): 'meanz_0.25',

#         ('ws', 3): 'meanz_0.63',
#         ('z500', 3): 'meanz_13.05',
#         ('z850', 3): 'meanz_4.81'}

"""
MODE = {('2t', 3): 'meanw_1.07',
        (167, 0, 3): 'meanw_1.07',
        ('msl', 3): 'meanw_0',
        (151, 0, 3): 'meanw_0',

        ('sd', 3): 'meanw_0.000125',
        (141, 0, 3): 'meanw_0.000125',

        ('sp', 3): 'meanw_0.00354004',
        (134, 0, 3): 'meanw_0.00354004',

        ('tp', 3): 'meanw_0.000125',
        (228, 0, 3): 'meanw_0.000125',

        ('ws', 3): 'meanw_1.34687',
        (10, 0, 3): 'meanw_1.34687',
        (10, 10, 3): 'meanw_1.34687',


        (129, 500, 3): 'meanw_0.004',
        (129, 850, 3): 'meanw_0.00549316',

        ('z500', 3): 'meanw_0.004',
        ('z850', 3): 'meanw_0.00549316',

        (228029, 0, 3): 'meanw_1',
        ('i10fg', 3): 'meanw_1',

        (164, 0, 3): 'meanw_1',
        ('tcc', 3): 'meanw_1',


        (255, 0, 3): 'meanw_1',
        ('logtp', 3): 'meanw_1',
        ('logsf', 3): 'meanw_1',
        (144, 0, 3): 'meanw_1',
        ('expsf', 3): 'meanw_1',
        ('exptp', 3): 'meanw_1',
        ('expsd', 3): 'meanw_1',


         ('g1sf', 3): 'meanw_1',
        ('g1tp', 3): 'meanw_1',
        ('g1sd', 3): 'meanw_1',


         ('g2sf', 3): 'meanw_1',
        ('g2tp', 3): 'meanw_1',
        ('g2sd', 3): 'meanw_1',

        (229, 0, 3): 'meanw_1',

        ('sf', 3): 'meanw_1',
        ('swh', 3): 'meanw_1',
        ('10u', 3): 'meanw_1',
        ('10v', 3): 'meanw_1',
        (165, 0, 3): 'meanw_1',
        (166, 0, 3): 'meanw_1',

        (140229, 0, 3): 'meanw_1',
        (140229, 3): 'meanw_1',

        }

NAME = {'tp': "Total precipitations",
        'ws': "10m wind speed",
        '2t': "Surface air temperature",
        'sp': "Surface pressure",
        'msl': "Mean sea level pressure",
        'sd': "Snow depth",
        'sd': "Snow depth",
        'z850': "Geopotential at 850 hPa",
        'z500': "Geopotential at 500 hPa"}

SCALE = {'ws': (1, 0, "m/s"),
         '2t': (1, -273.15, "&deg;C"),
         'tp': (1000, 0, "mm"),
         'g1tp': (1000, 0, "mm"),
         'g2tp': (1000, 0, "mm"),

         'sd': (100 / 0.2, 0, "cm"),  # Assumes %20 density
         'g1sd': (100 / 0.2, 0, "cm"),  # Assumes %20 density
         'g2sd': (100 / 0.2, 0, "cm"),  # Assumes %20 density

         'sd (exp)': (100 / 0.2, 0, "cm"),  # Assumes %20 density
         'z500': (0.0101971621297793, 0, "dam"),
         'z850': (0.0101971621297793, 0, "dam"),
         'msl': (0.01, 0, "hPa"),
         'sp': (0.01, 0, "hPa"),
         'tcc': (1, 0, '%'),
         'i10fg': (1, 0, "m/s"),
         'logtp': (1000, 0, "log(1+m)"),
         'exptp': (1000, 0, "exp(m)"),
         'sf': (1000, 0, 'mm'),
         'g1sf': (1000, 0, 'mm'),
         'g2sf': (1000, 0, 'mm'),
         'logsf': (1000, 0, "log(1+m)"),
         'expsf': (1000, 0, "exp(m)"),
         '10u': (1, 0, "m/s"),
         '10v': (1, 0, "m/s"),
         'swh': (1, 0, "m"),
         }


PARAMS = {
    'tp': 228,
}


def param(param):
    return PARAMS[param]


class DefaultRetriever(object):

    def execute(self, data):
        c = ecmwfapi.ECMWFService("mars")
        f, target = tempfile.mkstemp(".grib")
        os.close(f)
        c.execute(retrieve(data), target)
        field = GribFile(target).next()
        os.unlink(target)
        return field


class WindRetriever(object):

    def execute(self, data):
        c = ecmwfapi.ECMWFService("mars")
        f, target = tempfile.mkstemp(".grib")
        os.close(f)
        c.execute(retrieve(data), target)
        w = GribFile(target)
        u = w.next()
        v = w.next()
        q = np.sqrt(u.array * u.array + v.array * v.array)
        u.set_array(q)
        os.unlink(target)
        return u


class PrecipRetriever(object):

    def execute(self, data):
        c = ecmwfapi.ECMWFService("mars")
        f, target = tempfile.mkstemp(".grib")
        os.close(f)
        c.execute(retrieve(data), target)
        w = list(GribFile(target))
        if len(w) == 2:
            cp = w[0]
            lsp = w[1]
            q = cp.array + lsp.array
            cp.set_array(q)
            field = cp
        else:
            field = w[0]

        os.unlink(target)
        return field


RETRIEVER = {'ws': WindRetriever, 'tp': PrecipRetriever}


def mars(data):
    Retriever = RETRIEVER.get(data['param'], DefaultRetriever)
    r = Retriever()
    return r.execute(data)


def units(param):
    u = SCALE[param]
    return {"scale": u[0], "offset": u[1], "unit": u[2]}
"""


def params(f=lambda x: x):
    result = {}
    for k in SCALE.keys():
        result[name(k)] = f(k)
    return result


def variables():
    return sorted(SCALE.keys())


def area_around(lat, lon):
    n, w = int(lat * 2 + 0.5) * 0.5 + 8, int(lon * 2 + 0.5) * 0.5 - 8
    a = (n, w, n - 15.5, w + 15.5)
    return a


def wavelet_mode(param, level, depth=None):
    if depth is None:
        return MODE[(param, level)]
    else:
        return MODE[(param, level, depth)]


def name(param):
    return NAME.get(param, param)


def cache_file(*args):
    return os.path.join(ANALOGUES_FILES, *args)


def cache_data(*args):
    return os.path.join(ANALOGUES_DATA, *args)


def analogue_home(*args):
    return os.path.join(ANALOGUES_HOME, *args)


def data_path(*args):
    return analogue_home('data', *args)


def image_path(name):
    return analogue_home("latex", "images", name)


def latex_path(name):
    return analogue_home("latex", name)


def fingerprints_path(*args):
    return data_path("fingerprints", *args)


def validate_path(*args):
    return data_path("validate", *args)


def validate_json(**kwargs):
    return validate_path("%s/validate-%s-%s-%s-%s-%s.json" % (kwargs['domain'],
                                                              kwargs.get('distance', 'l2'),
                                                              kwargs['param'],
                                                              kwargs['depth'],
                                                              kwargs.get('wavelet', 'haar'),
                                                              kwargs['mode']))


def fingerprints_db(**kwargs):
    return fingerprints_path("%s/%s-%s/%s-%s.db" % (kwargs['domain'],
                                                    kwargs.get('wavelet', 'haar'),
                                                    kwargs['mode'],
                                                    kwargs['param'],
                                                    kwargs['depth']))


def fingerprints_available(domain):
    result = []
    for n in os.listdir(fingerprints_path(domain)):
        for p in os.listdir(fingerprints_path(n)):
            if p.endswith('.db'):
                q = n.split('-')
                r = p[:-3].split('-')
                result.append(dict(wavelet=q[0],
                                   domain=domain,
                                   mode=q[1], param=r[0], depth=int(r[1])))
    return result


def validate_available(domain):
    result = []

    for n in os.listdir(validate_path(domain)):

        if n.endswith(".json") and n.startswith("validate-"):
            x = n[:-5].split("-")
            if x[5].endswith('_'):
                x[5] += '-' + x[6]
            result.append(dict(distance=x[1],
                               param=x[2],
                               domain=domain,
                               depth=int(x[3]),
                               wavelet=x[4],
                               mode=x[5]))
    return result


####################################################################


if os.path.exists('/Users/baudouin/Dropbox'):
    from analogues.backend.sqlite import SqliteEngine
    cdsdb = SqliteEngine()
    ROOT = '/Users/baudouin/Dropbox/phd/data'
    CACHE = ROOT
else:
    from analogues.backend.postgres import PostgresEngine
    cdsdb = PostgresEngine()
    ROOT = '/cache/analogues'
    CACHE = '/cache/data'
