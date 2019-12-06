import numpy as np
import os
import subprocess


class MARSRetriever:

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

    def to_mars_request(self, requests, verb='retrieve'):
        result = [verb]
        for k, v in requests.items():
            if isinstance(v, (list, tuple)):
                v = '/'.join(v)
            result.append('%s=%s' % (k, v))
        return ',\n'.join(result)

    def mars_request(self):
        return self.to_mars_request(self.request)

    def execute(self, target):
        with open(target + '.r', 'w') as f:
            f.write(self.mars_request())
            f.write(',target="%s"' % (target,))

        assert subprocess.call(['/usr/local/bin/mars', target + '.r']) == 0
        os.unlink(target + '.r')


class SimpleRetriever(MARSRetriever):
    pass


class WindRetriever(MARSRetriever):

    def __init__(self, param):
        super().__init__(param)
        self.u = param.u
        self.v = param.v
        self.paramId = param.paramId

    def mars_request(self):
        reqs = []

        self.request['param'] = self.u
        self.request['fieldset'] = 'u'
        reqs.append(self.to_mars_request(self.request))

        self.request['param'] = self.v
        self.request['fieldset'] = 'v'
        reqs.append(self.to_mars_request(self.request))

        reqs.append("compute,formula='sqrt(u*u+v*v)',fieldset=ws")
        reqs.append("write,fieldset=ws")

        return '\n'.join(reqs)

    def execute(self, target):
        super().execute(target + '.tmp')

        if not os.path.exists(target + '.tmp'):
            return

        from grib import GribFile

        mode = 'w'
        for g in GribFile(target + '.tmp'):
            g.set('paramId', self.paramId)
            g.write(target, mode)
            mode = 'a'

        os.unlink(target + '.tmp')


class LogRetriever(MARSRetriever):

    def __init__(self, param):
        super().__init__(param)
        self.param = param.param
        self.paramId = param.paramId

    def mars_request(self):
        reqs = []

        self.request['param'] = self.param
        self.request['fieldset'] = 'x'
        reqs.append(self.to_mars_request(self.request))

        reqs.append("compute,formula='log(1+x)',fieldset=y")
        reqs.append("write,fieldset=y")

        return '\n'.join(reqs)

    def execute(self, target):
        super().execute(target + '.tmp')

        if not os.path.exists(target + '.tmp'):
            return

        from grib import GribFile

        mode = 'w'
        for g in GribFile(target + '.tmp'):
            g.set('paramId', self.paramId)
            g.write(target, mode)
            mode = 'a'

        os.unlink(target + '.tmp')


class GaussRetriever(MARSRetriever):

    def __init__(self, param):
        super().__init__(param)
        self.param = param.param
        # self.paramId = param.paramId
        self.sigma = param.sigma

    def execute(self, target):
        super().execute(target + '.tmp')

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


class ExpRetriever(MARSRetriever):

    def __init__(self, param):
        super().__init__(param)
        self.param = param.param
        self.paramId = param.paramId

    def mars_request(self):
        reqs = []

        self.request['param'] = self.param
        self.request['fieldset'] = 'x'
        reqs.append(self.to_mars_request(self.request))

        reqs.append("compute,formula='exp(x)',fieldset=y")
        reqs.append("write,fieldset=y")

        return '\n'.join(reqs)

    def execute(self, target):
        super().execute(target + '.tmp')

        if not os.path.exists(target + '.tmp'):
            return

        from grib import GribFile

        mode = 'w'
        for g in GribFile(target + '.tmp'):
            g.set('paramId', self.paramId)
            g.write(target, mode)
            mode = 'a'

        os.unlink(target + '.tmp')
