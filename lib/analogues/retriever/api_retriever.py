import cdsapi
import numpy as np
import os


DATASETS = {
    ('reanalysis', 'sfc'): "reanalysis-era5-single-levels",
    ('reanalysis', 'pl'): "reanalysis-era5-pressure-levels"
}


class APIRetriever:

    def __init__(self, param):
        self.request = {}
        param.to_mars(self.request)

    def domain(self, domain):
        domain.to_mars(self.request)

    def dataset(self, dataset):
        dataset.to_mars(self.request)

    def dates(self, dates):
        self.request['date'] = sorted(dates)

    def times(self, times):
        self.request['time'] = sorted(times)

    def retrieve(self, request, target):
        c = cdsapi.Client(debug=True)

        key = (request.get('dataset'), request.get('levtype'))

        try:
            r = c.retrieve(DATASETS[key], request)
            r.download(target)
        except Exception as e:
            if 'Request returned no data' not in repr(e):
                raise

    def execute(self, target):
        self.retrieve(self.request, target)


class SimpleRetriever(APIRetriever):
    pass


class GaussRetriever(APIRetriever):

    def __init__(self, param):
        super().__init__(param)
        self.param = param.param
        # self.paramId = param.paramId
        self.sigma = param.sigma

    def execute(self, target):
        self.retrieve(self.request, target + '.tmp')

        if not os.path.exists(target + '.tmp'):
            return

        from grib import GribFile
        from scipy.ndimage import gaussian_filter
        print("gaussian_filter ->", target, self.sigma)

        mode = 'w'
        for g in GribFile(target + '.tmp'):
            g.set('values', gaussian_filter(g.array, self.sigma))
            # g.set('paramId', self.paramId)
            g.write(target, mode)
            mode = 'a'

        os.unlink(target + '.tmp')


class WindRetriever(APIRetriever):

    def __init__(self, param):
        super().__init__(param)
        self.u = param.u
        self.v = param.v
        self.paramId = param.paramId

    def execute(self, target):
        self.request['param'] = self.u
        self.retrieve(self.request, target + '-u')

        self.request['param'] = self.v
        self.retrieve(self.request, target + '-v')

        if not os.path.exists(target + '-u'):
            return

        if not os.path.exists(target + '-v'):
            return

        from grib import GribFile
        us = GribFile(target + '-u')
        vs = GribFile(target + '-v')

        mode = 'w'
        for u, v in zip(us, vs):
            assert u.date == v.date
            assert u.time == v.time

            du = u.array
            dv = v.array
            ws = np.sqrt(du * du + dv * dv)

            u.set('values', ws)
            u.set('paramId', self.paramId)
            u.write(target, mode)
            mode = 'a'

        more_u = True
        more_v = True
        try:
            next(us)
        except StopIteration:
            more_u = False

        try:
            next(vs)
        except StopIteration:
            more_v = False

        assert not more_u and not more_v

        os.unlink(target + '-u')
        os.unlink(target + '-v')


class LogRetriever(APIRetriever):

    def __init__(self, param):
        raise NotImplementedError()


class ExpRetriever(APIRetriever):

    def __init__(self, param):
        raise NotImplementedError()
