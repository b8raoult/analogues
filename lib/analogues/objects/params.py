
import math


PARAMS = {}

CONVERT = {
    ('m', 'mm'): (1000, 0),
    ('K', 'degC'): (1, -273.15),
    ('Pa', 'hPa'): (0.01, 0),
    ('m2/s2', 'dam'): (0.0101971621297793, 0),
}

HTML = {
    "degC": "&deg;C",
}

LATEX = {
    "m/s": "m s^{-1}",
    "m2/s2": "m^2 s^{-2}",
    "%": r'\%',
}

LATEX_NAMES = {'2t': 'twot',
               '10u': 'tenu',
               '10v': 'tenv',
               'z500': 'zfive',
               'z850': 'zeight',
               'i10fg': 'tenfg',
               }

NORMALISE = {
    'dam': lambda x: int(x + 0.5),
    'hPa': lambda x: int(x + 0.5),
    'degC': lambda x: int(x * 10.0 + 0.5) / 10.0,
    'm': lambda x: int(x * 10.0 + 0.5) / 10.0,
    '%': lambda x: int(x * 10.0 + 0.5) / 10.0,
    'm/s': lambda x: int(x * 10.0 + 0.5) / 10.0,
    'mm': lambda x: int(x * 10000.0 + 0.5) / 10000.0,
}

DEFAULT_METHODS = {
#     "10u": 0,
#     "10v": 9,
#     "2t": 9,
#     "msl": 10,
#     "sd": 13,
#     "sf": 7,
#     "swh": 5,
#     "tcc": 10,
#     "tp": 7,
#     "ws": 0,
#     "z500": 5,
#     "z850": 5
}


class Units:

    def __init__(self, units):
        self.offset = 0
        self.scale = 1
        if isinstance(units, str):
            self.units = units
            self.want = units
        if isinstance(units, (list, tuple)):
            self.units = units[0]
            self.want = units[1]
            self.scale, self.offset = CONVERT[(units[0], units[1])]
            if len(units) == 3:
                self.scale *= units[2]

    @property
    def html(self):
        return HTML.get(self.want, self.want)

    @property
    def latex(self):
        print('-----')
        return LATEX.get(self.units, self.units)

    def to_json(self):
        return {"scale": self.scale,
                "offset": self.offset,
                "unit": self.html}

    def __repr__(self):
        return "Unit(%s,%s,%s,%s)" % (self.units, self.scale, self.offset, self.want)

    def normalise(self, number):

        def _(x):
            return '%g' % (number,)

        return str(NORMALISE.get(self.want, _)(number))


class Param:

    def __init__(self,
                 name,
                 title,
                 contour,
                 zindex,
                 units,
                 param=None):
        self.name = name
        self.title = title
        self.contour = contour
        self.zindex = zindex
        self.param = param
        self.units = Units(units)
        if param is None:
            self.param = name

    @classmethod
    def lookup(cls, name):
        return PARAMS[name]

    def retriever(self, factory):
        return factory.simple_retriever(self)

    def fingerprinting_method(self, field, n=0):
        from ..distances import METHODS
        from ..distances.method import Method
        if n is None:
            n = DEFAULT_METHODS.get(self.name, 0)
        if isinstance(n, Method):
            return n
        return METHODS[int(n)](field)

    @property
    def latex(self):
        name = self.name
        name = LATEX_NAMES.get(name, name)
        return r'\%s{}' % (name[0].upper() + name[1:],)

    def normalise(self, number):
        return self.units.normalise(number)


class PlParam(Param):

    levtype = 'pl'

    def __init__(self,
                 name,
                 level,
                 title,
                 contour,
                 zindex,
                 units,
                 param):
        super(PlParam, self).__init__(name,
                                      title,
                                      contour,
                                      zindex,
                                      units,
                                      param)
        self.level = level

    def to_mars(self, request):
        request['param'] = self.param
        request['level'] = str(self.level)
        request['levtype'] = 'pl'


class SfcParam(Param):

    def to_mars(self, request):
        request['param'] = self.param
        request['levtype'] = 'sfc'


class WaveParam(SfcParam):
    pass


class Wind(Param):

    u = '10u'
    v = '10v'
    paramId = 10

    def retriever(self, factory):
        return factory.wind_retriever(self)

    def to_mars(self, request):
        request['levtype'] = 'sfc'


PARAMS['ws'] = Wind('ws',
                    title='10m wind speed',
                    contour='sh_red_f5t70lst',
                    zindex=2,
                    units="m/s")


class LogParam(Param):

    paramId = 255

    def retriever(self, factory):
        return factory.log_retriever(self)

    def to_mars(self, request):
        request['levtype'] = 'sfc'


class ExpParam(Param):

    paramId = 255

    def retriever(self, factory):
        return factory.exp_retriever(self)

    def to_mars(self, request):
        request['levtype'] = 'sfc'


class GaussParam1(Param):

    # paramId = 255
    sigma = 1

    def retriever(self, factory):
        return factory.gauss_retriever(self)

    def to_mars(self, request):
        request['levtype'] = 'sfc'
        request['param'] = self.param


class GaussParam2(Param):

    # paramId = 255
    sigma = 1

    def retriever(self, factory):
        return factory.gauss_retriever(self)

    def to_mars(self, request):
        request['levtype'] = 'sfc'
        request['param'] = self.param


# This is sh_blured_f05t300lst devided by 10 as ERA5 is just 1 hour accumulation
f = 6.0
# f = 12.0
# f = 3.0
# f = 1

sh_blured_f05t300lst = {
    "contour_highlight": "off",
    "contour_hilo": "off",
    "contour_label": "off",
    "contour_legend_text": "Contour shade (Range: 0.5 / 250, with isolines)",
    "contour_level_list": [x / f for x in [0.5, 2, 4, 10, 25, 50, 100, 250]],
    "contour_level_selection_type": "level_list",
    "contour_shade": "on",
    "contour_shade_colour_list": ["cyan", "greenish_blue", "blue", "bluish_purple", "magenta", "orange", "red", "charcol"],
    "contour_shade_colour_method": "list",
    "contour_internal_reduction_factor": 4,
    "contour_shade_method": "area_fill",
    "contour_shade_min_level": 0.5 / f
}

sh_grnvio_f1t100lst = {
    "contour": "off",
    "contour_highlight": "off",
    "contour_hilo": "off",
    "contour_label": "off",
    "contour_label_frequency": 1,
    "contour_legend_text": "Contour shade (Range: 1.0 / 250, no isolines)",
    "contour_level_list": [x / f for x in [1, 2.5, 6, 15, 40, 100, 250]],
    "contour_level_selection_type": "level_list",
    "contour_method": "linear",
    "contour_shade": "on",
    "contour_shade_cell_resolution": 40.0 / f,
    "contour_shade_colour_list": ["rgb(0.5,1,0.7)",
                                  "rgb(0.4,0.9,0.6)",
                                  "rgb(0.3,0.83,0.6)",
                                  "rgb(0.43,0.76,0.7)",
                                  "rgb(0.56,0.69,0.8)",
                                  "rgb(0.7,0.62,0.9)"],
    "contour_shade_colour_method": "list",
    "contour_shade_method": "area_fill",
    "contour_shade_min_level": 1.0 / f,
    "legend": "on"
}

PARAMS['tp'] = SfcParam('tp',
                        'Total precipitations',
                        sh_blured_f05t300lst,
                        zindex=5,
                        units=['m', 'mm'])

PARAMS['sf'] = SfcParam('sf',
                        'Snowfall',
                        sh_grnvio_f1t100lst,
                        zindex=5,
                        units=['m', 'mm'])

PARAMS['2t'] = SfcParam('2t',
                        'Surface air temperature',
                        contour=None,
                        zindex=0,
                        units=['K', 'degC'])

PARAMS['msl'] = SfcParam('msl',
                         'Mean sea level pressure',
                         contour=None,
                         zindex=10,
                         units=['Pa', 'hPa'])

# PARAMS['sp'] = SfcParam('sp',
#                          'Surface pressure',
#                          contour=None,
#                          zindex=10,
#                          units=['Pa', 'hPa'])


snow_contour = {
    "contour": "off",
    "contour_hilo": "off",
    "contour_label": "off",
    "contour_level_list": [0.001,
                           0.002,
                           0.005,
                           0.01,
                           0.015,
                           0.02,
                           0.03,
                           0.04,
                           0.05,
                           0.07,
                           0.1,
                           0.2,
                           0.5,
                           10.0],
    "contour_level_selection_type": "level_list",
    "contour_reference_level": 0.01,
    "contour_shade": "on",
    "contour_shade_colour_list": ["rgb(0.45,0.6,0.45)",
                                  "rgb(0.59,0.75,0.59)",
                                  "rgb(0.73,0.84,0.73)",
                                  "rgb(0.87,0.87,0.87)",
                                  "rgb(0.94,0.94,0.94)",
                                  "rgb(1,1,1)",
                                  "rgb(0.9,0.95,1)",
                                  "rgb(0.8,0.9,1)",
                                  "rgb(0.67,0.83,1)",
                                  "rgb(0.5,0.75,1.0)",
                                  "rgb(0.85,0.8,1)",
                                  "rgb(0.75,0.68,1)",
                                  "rgb(0.6,0.5,1)"],
    "contour_shade_colour_method": "list",
    "contour_shade_label_blanking": "off",
    "contour_shade_max_level": 10.0,
    "contour_shade_method": "area_fill",
                            "contour_shade_min_level": 0.001}

PARAMS['sd'] = SfcParam('sd',
                        'Snow depth',
                        snow_contour,
                        zindex=1,
                        units=['m', 'mm', 1. / 0.2])

# PARAMS['sp'] = SfcParam('sp', 'Surface pressure')
PARAMS['z850'] = PlParam('z850',
                         param='z',
                         level=850,
                         title='Geopotential at 850 hPa',
                         contour=None,
                         units=['m2/s2', "dam"],
                         zindex=10)

PARAMS['z500'] = PlParam('z500',
                         param='z',
                         level=500,
                         title='Geopotential at 500 hPa',
                         contour=None,
                         units=['m2/s2', "dam"],
                         zindex=10)

PARAMS['tcc'] = SfcParam('tcc',
                         'Total cloud cover',
                         contour=None,
                         units='%',
                         zindex=100)

# PARAMS['i10fg'] = SfcParam('i10fg',
#                            '10m wind gust',
#                            contour=None,
#                            zindex=2)

PARAMS['swh'] = SfcParam('swh',
                         'Significant wave height',
                         param=140229,
                         contour=None,
                         units='m',
                         zindex=100)

winds = dict(legend="on",
             contour_level_selection_type="level_list",
             contour_level_list=[-20., -10., -5., -2.5, -1., -0.5, 0., 0.5, 1, 2.5, 5., 10., 20., 50.],
             contour_line_colour="grey",
             contour_line_thickness=2,
             contour_label="off",
             contour_highlight="off",
             contour_shade="on",
             contour_shade_method="area_fill",
             contour_shade_colour_method="calculate",
             contour_shade_max_level_colour="red",
             contour_shade_min_level_colour="blue",
             contour_shade_colour_direction="clockwise")

PARAMS['10u'] = SfcParam('10u',
                         '10m zonal wind',
                         contour=winds,
                         units='m/s',
                         zindex=100)

PARAMS['10v'] = SfcParam('10v',
                         '10m meridional wind',
                         contour=winds,
                         units='m/s',
                         zindex=100)


def new_contour(c, f):

    d = dict(**c)

    for n in ('contour_reference_level',
              'contour_shade_min_level',
              'contour_shade_max_level',
              'contour_level_list'):
        if n in c:
            if isinstance(c[n], (list, tuple)):
                d[n] = [f(x) for x in c[n]]
            else:
                d[n] = f(c[n])

    return d


def log1p(x):
    return math.log1p(x / 1000.0)


def exp(x):
    return math.exp(x / 1000.0)


# PARAMS['logtp'] = LogParam('logtp',
#                            'Total precipitations (log)',
#                            contour=new_contour(sh_blured_f05t300lst, log1p),
#                            zindex=5,
#                            method=0,
#                            param='tp')


# PARAMS['logsf'] = LogParam('logsf',
#                            'Snowfall (log)',
#                            contour=new_contour(sh_grnvio_f1t100lst, log1p),
#                            zindex=5,
#                            method=0,
#                            param='sf')


# PARAMS['expsf'] = ExpParam('expsf',
#                            'Snowfall (exp)',
#                            contour=new_contour(sh_grnvio_f1t100lst, exp),
#                            zindex=5,
#                            method=0,
#                            param='sf')
# # update fingerprint_logsf_uk_era5 set updated = '2000-01-01' where extract(hour from valid_date) = 12;


# PARAMS['exptp'] = ExpParam('exptp',
#                            'Total precipitations (exp)',
#                            contour=new_contour(sh_blured_f05t300lst, exp),
#                            zindex=5,
#                            method=0,
#                            param='tp')


# PARAMS['expsd'] = ExpParam('expsd',
#                            'Snow depth (exp)',
#                            contour=new_contour(snow_contour, exp),
#                            zindex=1,
#                            param='sd')

if False:

    PARAMS['g1sf'] = GaussParam1('g1sf',
                                 'Snowfall (g1)',
                                 contour=sh_grnvio_f1t100lst,
                                 zindex=5,
                                 method=0,
                                 param='sf')
    # update fingerprint_logsf_uk_era5 set updated = '2000-01-01' where extract(hour from valid_date) = 12;

    PARAMS['g1tp'] = GaussParam1('g1tp',
                                 'Total precipitations (g1)',
                                 contour=sh_blured_f05t300lst,
                                 zindex=5,
                                 method=0,
                                 param='tp')

    PARAMS['g1sd'] = GaussParam1('g1sd',
                                 'Snow depth (g1)',
                                 contour=snow_contour,
                                 zindex=1,
                                 param='sd')

    PARAMS['g2sf'] = GaussParam2('g2sf',
                                 'Snowfall (g2)',
                                 contour=sh_grnvio_f1t100lst,
                                 zindex=5,
                                 method=0,
                                 param='sf')
    # update fingerprint_logsf_uk_era5 set updated = '2000-01-01' where extract(hour from valid_date) = 12;

    PARAMS['g2tp'] = GaussParam2('g2tp',
                                 'Total precipitations (g2)',
                                 contour=sh_blured_f05t300lst,
                                 zindex=5,
                                 method=0,
                                 param='tp')

    PARAMS['g2sd'] = GaussParam2('g2sd',
                                 'Snow depth (g2)',
                                 contour=snow_contour,
                                 zindex=1,
                                 param='sd')


_ = """
UPDATE fingerprint_logsf_uk_era5
set updated = '2000-01-01' where extract(hour from valid_date) = 12;
"""

_ = """
UPDATE fingerprint_10v_uk_era5  set updated = '2000-01-01' where strftime('%H', valid_date) = '12';
"""

if __name__ == "__main__":
    print(PARAMS)
