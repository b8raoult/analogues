
import os
import similarities
from sqlalchemy import text

from analogues.conf import cdsdb, ROOT

from analogues.fingerprint import FingerPrint

import numpy as np

import datetime
import json

from analogues.objects.domains import Domain, DEFAULT_DOMAIN
from analogues.objects.datasets import DEFAULT_DATASET

from analogues.objects.params import Param
from analogues.objects.matrices import START_DATE, END_DATE, L2_DATES, NEWL2
from analogues.objects.matrices import FingerprintDistanceMatrix, FullDistanceMatrix
from analogues.objects.matrices import ClusterMatrix, FullDistanceMatrix

from analogues.objects.mixins.sql import FieldSQL
from analogues.objects.mixins.matrix import FieldMatrix
from analogues.objects.mixins.grib import FieldGrib
from analogues.objects.mixins.clim import FieldClim

RANGE = {
    'tp': (0, 0.02),
}


class Field(FieldSQL, FieldMatrix, FieldClim, FieldGrib):

    def __init__(self,
                 param,
                 domain=DEFAULT_DOMAIN,
                 dataset=DEFAULT_DATASET,
                 **ignore):
        self.param = param
        self.domain = domain
        self.dataset = dataset

        FieldSQL.__init__(self)
        FieldMatrix.__init__(self)
        FieldClim.__init__(self)
        FieldGrib.__init__(self)

        # self._dates = None

        # self._distance_table = None

        # self._SELECT_SAMPLE = None
        # self._SELECT_FIRST_SAMPLE = None

        # self._COUNT_CLOSER_L2 = None

        # self._smoothness2_average_no_constants = None

        # # self._distance_matrix_cache = None

        # self._cluster = 0
        # self._compression = 0

        # self._range = RANGE.get(self.param, (0, 0))

    @property
    def to_path(self):
        return [self.param, self.domain, self.dataset]

    @property
    def cut_threshold(self):
        single = {
            "ws": 85.37910356214117,
            "tp": 0.01675601160241746,
            "sf": 0.0017107379207884073,
            "2t": 45.63821951205714,
            "msl": 12058.854894848018,
            "sd": 0.03156383768653816,
            "z850": 9066.901386038155,
            "z500": 12148.2864841096,
            "tcc": 10.751291826199463,
            "swh": 20.6011499631732,
            "10u": 113.13670884756546,
            "10v": 107.6591672632189
        }

        return single[self.param]

    def distance_path(self):
        return self.path("distance")

    def __repr__(self):
        return "Field(%s,%s,%s)" % (self.param, self.domain, self.dataset)

    def fingerprinting_method(self, n=None):
        return Param.lookup(self.param).fingerprinting_method(self, n)

    def path(self, what):
        return "{root}/{what}-{param}-{domain}-{dataset}.npy".format(root=ROOT,
                                                                     what=what,
                                                                     param=self.param,
                                                                     domain=self.domain,
                                                                     dataset=self.dataset)

    @property
    def zindex(self):
        return Param.lookup(self.param).zindex

    @property
    def title(self):
        return Param.lookup(self.param).title

    @property
    def alpha_range(self):
        return Param.lookup(self.param).range

    @property
    def units(self):
        return Param.lookup(self.param).units

    @property
    def latex(self):
        return Param.lookup(self.param).latex

    def normalise(self, number):
        return Param.lookup(self.param).normalise(number)

    def check_range(self, mn, mx):
        return
        n, x = self._range
        if mn < n:
            raise Exception("%s %s out of range %s" % (self, mn, self._range))
        if mx > x:
            raise Exception("%s %s out of range %s" % (self, mx, self._range))

    @property
    def metadata(self):
        return {"contour": Param.lookup(self.param).contour}

    @property
    def COUNT_CLOSER_L2(self):
        if self._COUNT_CLOSER_L2 is None:
            self._COUNT_CLOSER_L2 = text("""
            SELECT COUNT(*) FROM {table}
            WHERE l2<:l2 and date1 = :date1 and date2 != :date1
            """.format(table=self.distance_table))
        return self._COUNT_CLOSER_L2

    def Xclosest_l2(self, query_date):
        i = (query_date - START_DATE).days
        dm = self.distance_matrix

        best = None
        k = None
        for j in range(0, L2_DATES):
            if i != j and np.isfinite(dm[j, i]):
                if best is None:
                    best = dm[j, i]
                    k = j
                elif dm[j, i] < best:
                    best = dm[j, i]
                    k = j

        return best, START_DATE + datetime.timedelta(days=k, hours=12)

    def Xfurthest_l2(self, query_date):
        i = (query_date - START_DATE).days
        dm = self.distance_matrix
        best = None
        k = None
        for j in range(0, L2_DATES):
            if i != j and np.isfinite(dm[j, i]):
                if best is None:
                    best = dm[j, i]
                    k = j
                elif dm[j, i] > best:
                    best = dm[j, i]
                    k = j

        return best, START_DATE + datetime.timedelta(days=k, hours=12)

    def count_closer_l2(self, query_date, l2):
        i = (query_date - START_DATE).days
        dm = self.distance_matrix
        x = dm[:, i:i + 1] < l2
        x[i, :] = False  # Don't count self
        return np.count_nonzero(x)

    def get_closer_l2(self, query_date, l2):
        i = (query_date - START_DATE).days
        dm = self.distance_matrix
        x = dm[:, i:i + 1] < l2
        x[i, :] = False  # Don't count self
        for k, v in enumerate(x.flatten()):
            if v:
                yield (START_DATE + datetime.timedelta(days=k, hours=12), dm[k, i])

    def score3(self, query_date, fingerprint_closest_date, dm):
        l2_closest, l2_closest_date = dm.closest(query_date)
        s = dm.distance(fingerprint_closest_date, l2_closest_date)
        return s

    def score4(self, query_date, fingerprint_closest_date, dm):
        l2_closest, l2_closest_date = dm.closest(query_date)
        l2_furthest, _ = dm.furthest(l2_closest_date)
        s = dm.distance(fingerprint_closest_date, l2_closest_date)
        return s / l2_furthest

    def score5(self, query_date, fingerprint_closest_date, dm):
        l2_closest, l2_closest_date = dm.closest(query_date)
        s = dm.distance(fingerprint_closest_date, l2_closest_date)
        return s / l2_closest

    score = score3
    score_version = 3

    @property
    def contour(self):
        return self.metadata['contour']

    def Xcompute_l2_distances(self, dates, bar):
        global NEWL2
        import time
        # Force loading
        start = time.time()
        self.distance_matrix

        NEWL2 = 0
        for i, date1 in enumerate(dates):
            for date2 in dates:
                self.l2_distance(date1, date2)
            bar.update(1)
        print("NEW L2", NEWL2, "elapsed", time.time() - start)
        return NEWL2

    def Xall_possible_dates(self):
        dates = []
        for j in range(0, L2_DATES):
            dates.append(START_DATE + datetime.timedelta(days=j, hours=12))
        return dates

    def Xl2_distance(self, date1, date2, dm=None):
        global NEWL2

        assert date1.hour == 12
        assert date2.hour == 12

        if dm is None:
            dm = self.distance_matrix

        i = (date1 - START_DATE).days
        j = (date2 - START_DATE).days

        l2 = dm[i, j]

        if np.isfinite(l2):
            return l2

        field1 = self.array(date1)
        field2 = self.array(date2)

        l2 = DISTANCE(field1, field2)
        NEWL2 += 1

        # print('compute_l2_distances', date1, date2, l2)
        # global UPDATE_DISTANCES
        assert self.UPDATE_DISTANCES

        dm[i, j] = l2
        dm[j, i] = l2

        return l2

    def Xl2_sorted_distances(self, date):
        i = (date - START_DATE).days
        dm = self.distance_matrix
        x = dm[:, i:i + 1]
        return sorted((v, START_DATE + datetime.timedelta(days=k, hours=12), k) for k, v in enumerate(x.flatten()) if k != i and np.isfinite(v))

    def fingerprint_distance_matrix(self, method, reference=None, readonly=True):
        if reference is None:
            reference = self.full_distance_matrix()
        return FingerprintDistanceMatrix(self,
                                         self.fingerprinting_method(method),
                                         reference,
                                         readonly=readonly)

    def full_distance_matrix(self, readonly=True):
        return FullDistanceMatrix(self, self.distance_path(), readonly=readonly)

    def cluster_distance_matrix(self, level, reference=None, readonly=True):
        if reference is None:
            reference = self.full_distance_matrix()

        return ClusterMatrix(self, reference, level, readonly=True)

    def Xcompression(self, depth, cluster=0):

        if cluster:
            self.cluster(cluster)

        training = self.distance_path("training-compression-%s-%s" % (depth, cluster))
        if os.path.exists(training):
            distance = self.distance_path()
            ts = os.stat(training)
            td = os.stat(distance)
            if td.st_mtime > ts.st_mtime:
                print("Removing", training)
                os.unlink(training)

        size = L2_DATES
        oldname = None
        if os.path.exists(training):
            mode = 'r'
        else:
            mode = 'w+'
            oldname = training
            training += '.tmp'

        try:
            print('load', training, mode)
            self._distance_matrix_path = training

            tm = np.memmap(training,
                           dtype=np.float64,
                           mode=mode,
                           shape=(size, size))
            if mode == 'w+':

                wavelet = 'haar'
                mode = 'full'
                dates = self.distance_dates()
                fingerprints = {}

                tm[:] = np.inf

                print("Compute fingerprints", depth, len(dates))
                for date in dates:
                    data = self.array(date)
                    finger = FingerPrint(data, depth, wavelet, mode)
                    fingerprints[date] = finger
                print("Done")

                print("Compute distances", depth, len(dates))

                for i in range(0, L2_DATES - 1):
                    tm[i, i] = 0
                    d1 = START_DATE + datetime.timedelta(days=i, hours=12)
                    if d1 in fingerprints:
                        f1 = fingerprints[d1]
                        for j in range(i + 1, L2_DATES):
                            d2 = START_DATE + datetime.timedelta(days=j, hours=12)
                            if d2 in fingerprints:
                                f2 = fingerprints[d2]
                                tm[i, j] = tm[j, i] = f1.distance(f2)
                print("Done")

        except Exception as e:
            print(e)
            os.unlink(training)
            raise

        self._training_matrix = tm
        self._distance_matrix = self._training_matrix

        if oldname:
            os.rename(training, oldname)
            self._distance_matrix_path = oldname

    def Xdistances_stats(self):
        self.distance_matrix
        distance = self._distance_matrix_path
        stats = distance + '.stats.json'
        if os.path.exists(stats):
            ts = os.stat(stats)
            td = os.stat(distance)
            if td.st_mtime > ts.st_mtime:
                print("Removing", stats)
                os.unlink(stats)

        if os.path.exists(stats):
            with open(stats) as f:
                return json.loads(f.read())

        print("Computing stats")
        dists = self.all_distances()
        s = dict(median=np.median(dists),
                 std=np.std(dists),
                 maximum=np.amax(dists),
                 minimum=np.amin(dists),
                 mean=np.mean(dists))

        with open(stats, "w") as f:
            f.write(json.dumps(s))

        return s

    def matches(self, fp, extremes=False, limit=12, use_l2=False, field=None, method=None):

        if use_l2:

            result = ((similarities.L2(field, self.array(d)), d) for d in self.dates)

            result = sorted(result, reverse=extremes)
            result = result[:limit]
            return [(b, a) for (a, b) in result]

        d = {}
        fp.to_db(d)

        order = {False: 'ASC', True: 'DESC'}
        match = text(self.fingerprinting_method(method).sql_text(table=self.fingerprint_table,
                                                                 limit=limit,
                                                                 order=order[extremes]))

        print(match)
        print(d)
        with cdsdb.begin() as connection:
            return [(cdsdb.sql_to_datetime(a), b) for (a, b) in connection.execute(match, **d).fetchall()]

    def matches2(self, other, fp1, fp2, weigths, limit=1000, extremes=False, use_l2=False, field1=None, field2=None):

        cnt = None
        while True:

            dates1 = [a[0] for a in self.matches(fp1,
                                                 extremes=extremes,
                                                 limit=limit,
                                                 use_l2=use_l2,
                                                 field=field1)]
            dates2 = [a[0] for a in other.matches(fp2,
                                                  extremes=extremes,
                                                  limit=limit,
                                                  use_l2=use_l2,
                                                  field=field2)]

            if len(dates1) == cnt:
                break

            cnt = len(dates1)

            common = set(dates1).intersection(dates2)

            # print('XXXXXXXXXXXXX', cnt, len(n))

            if common:

                score = {}
                for a in common:
                    score[a] = 0

                for i, a in enumerate(dates1):
                    if a in common:
                        score[a] += i * weigths[0]

                for i, a in enumerate(dates2):
                    if a in common:
                        score[a] += i * weigths[1]

                # dates1 = [(a, 0) for i, a in enumerate(dates1) if a in common]
                # dates2 = [(a, 0) for i, a in enumerate(dates2) if a in common]

                return [(a, 0) for a in sorted(common, key=lambda k: score[k])]

            limit += 1000

        return []

    @property
    def area(self):
        return Domain.lookup(self.domain).area
