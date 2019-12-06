import os
import datetime
import numpy as np
from tqdm import tqdm
import pickle

from similarities import L2


START_DATE = datetime.datetime(1979, 1, 1)
END_DATE = datetime.datetime(2018, 12, 31)
L2_DATES = (END_DATE - START_DATE).days + 1
NEWL2 = 0


EMPTY_DISTANCE = np.empty((L2_DATES, 1))
EMPTY_DISTANCE[:] = np.inf


class DistanceMatrix:

    def __init__(self,
                 field,
                 path,
                 reference=None,
                 readonly=True):
        self._path = path
        self._reference = reference
        self._matrix = None
        self._readonly = readonly
        self._field = field
        self._dates = None

        if reference is not None:
            reference.matrix  # Trigger update

    def __repr__(self):
        return "%s[%s]" % (self.__class__.__name__, os.path.basename(self._path))

    @property
    def matrix(self):
        if self._matrix is None:

            if self._reference:
                if os.path.exists(self._path):
                    ts = os.stat(self._path)
                    td = os.stat(self._reference._path)

                    if td.st_mtime > ts.st_mtime:
                        print(self, self._reference, "younger than", self._path)
                        print(self, "Removing", self._path)
                        os.unlink(self._path)

            size = L2_DATES
            path = self._path

            if os.path.exists(self._path):
                if self._readonly:
                    mode = 'r'
                else:
                    mode = 'r+'
            else:
                mode = 'w+'
                path = path + '.tmp.npy'

            self._matrix = np.memmap(path,
                                     dtype=np.float64,
                                     mode=mode,
                                     shape=(size, size))
            if mode == 'w+':
                self._matrix[:] = np.inf
                print(self, "Populate", path)
                self.populate(self._matrix)

            if path != self._path:
                os.rename(path, self._path)

            # count = (self._matrix < np.inf).sum()
            # print(self, 'Values {:,} out of {:,}'.format(count, self._matrix.size))
            print(self, 'loaded', mode)
        return self._matrix

    @property
    def dates(self):
        if self._dates is None:
            pass

    def check(self):
        dm = self.matrix
        assert np.array_equal(dm, np.transpose(dm))
        for i in range(0, L2_DATES):
            assert dm[i, i] == 0

    def populate(self, dm):
        pass

    def date_to_index(self, date):
        return (date - START_DATE).days

    def index_to_date(self, index):
        return START_DATE + datetime.timedelta(days=index, hours=12)

    def closest(self, query_date):
        i = self.date_to_index(query_date)
        dm = self.matrix

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

        return best, self.index_to_date(k)

    def furthest(self, query_date):
        i = self.date_to_index(query_date)
        dm = self.matrix
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

                return best, self.index_to_date(k)

    def sum_distances(self, date):
        dm = self.matrix
        i = self.date_to_index(date)
        x = dm[i, :]
        return x[x < np.inf].sum()

    def distance(self, date1, date2):
        global NEWL2

        assert date1.hour == 12
        assert date2.hour == 12

        dm = self.matrix

        i = self.date_to_index(date1)
        j = self.date_to_index(date2)

        l2 = dm[i, j]

        if np.isfinite(l2):
            return l2

        assert not self._readonly, (date1, date2)

        l2 = self.compute_distance(date1, date2)
        NEWL2 += 1

        # print('compute_l2_distances', date1, date2, l2)
        # global UPDATE_DISTANCES

        dm[i, j] = l2
        dm[j, i] = l2

        return l2

    def all_distances(self):
        from scipy.spatial.distance import squareform
        dm = self.matrix

        distance = self._path
        saved = self.derived_path(distance, '.npy', 'distances')
        if os.path.exists(saved):
            ts = os.stat(saved)
            td = os.stat(distance)
            if td.st_mtime > ts.st_mtime:
                print(self, distance, datetime.datetime.fromtimestamp(td.st_mtime).strftime('%Y-%m-%d %H:%M:%S'))
                print(self, saved, datetime.datetime.fromtimestamp(ts.st_mtime).strftime('%Y-%m-%d %H:%M:%S'))
                print(self, "Removing", saved)
                os.unlink(saved)

        if os.path.exists(saved):
            print(self, "Using", saved)
            return np.load(saved)

        print(self, "No cache", saved)

        print(self, "Computing distances",)

        r = squareform(dm)
        r = r[r != np.inf]

        print(self, 'Save', saved, r.shape)
        np.save(saved, r)
        print(r)
        return r

    def unique_distances(self):
        return np.unique(self.all_distances())

    def distance_dates(self):
        return [self.index_to_date(i) for i in sorted(self.date_indexes())]

    def derived_path(self, path, ext, *args):
        base, _ = os.path.splitext(path)
        return '-'.join([str(x) for x in [base, 'derived'] + list(args)]) + ext


class FullDistanceMatrix(DistanceMatrix):

    def compute_distance(self, date1, date2):

        field1 = self._field.array(date1)
        field2 = self._field.array(date2)

        return L2(field1, field2)

    def date_indexes(self):
        return range(0, L2_DATES)


class FingerprintDistanceMatrix(DistanceMatrix):

    def __init__(self, field, method, reference, readonly=True):

        self._method = method
        self._reference = reference
        method = '-'.join([str(x) for x in method.to_path])
        path = self.derived_path(reference._path, '.npy', 'fingerprint', method)
        DistanceMatrix.__init__(self, field, path, reference, readonly)

    def populate(self, dm):

        print(self, 'Reference', self._reference)

        dates = self._reference.distance_dates()
        method = self._method
        alpha = method.alpha
        fingerprints = self._field.fingerprints()

        with tqdm(total=len(dates), desc='fingerprint-populate') as bar:

            for i, d1 in enumerate(dates):
                (r1, s1) = fingerprints[d1]
                k = self.date_to_index(d1)
                for j in range(i + 1, len(dates)):
                    d2 = dates[j]
                    (r2, s2) = fingerprints[d2]
                    m = self.date_to_index(d2)
                    dm[k, m] = dm[m, k] = method.fingerprint_distance(r1, s1, r2, s2, alpha)

                bar.update(1)

        for i in range(0, L2_DATES):
            dm[i, i] = 0

    def date_indexes(self):
        return self._reference.date_indexes()


class ThinMatrix(DistanceMatrix):

    def __init__(self,
                 field,
                 reference,
                 level,
                 readonly=False):

        self._level = level
        path = self.derived_path(reference._path, '.npy', 'thin', level)
        self._reference = reference
        DistanceMatrix.__init__(self, field, path, reference, readonly)

    def populate(self, dm):

        print(self, 'populate', 'copy reference')
        dm[:] = self._reference.matrix

        epsilons = self._reference.unique_distances()
        # dates = self._reference.distance_dates()

        if self._level < 0:
            eps = self._field.cut_threshold
        else:
            eps = epsilons[self._level]

        print(self, 'populate', eps)
        print(self, 'count inf', (dm < np.inf).sum())
        print(self, 'count eps', (dm <= eps).sum())
        dm[dm <= eps] = np.inf
        for i in range(0, L2_DATES):
            dm[i, i] = 0

        print(self, 'count inf', (dm < np.inf).sum())

    def date_indexes(self):
        dm = self.matrix

        distance = self._path
        saved = self.derived_path(distance, '.pickle', 'dates')
        if os.path.exists(saved):
            ts = os.stat(saved)
            td = os.stat(distance)
            if td.st_mtime > ts.st_mtime:
                print(self, distance, datetime.datetime.fromtimestamp(td.st_mtime).strftime('%Y-%m-%d %H:%M:%S'))
                print(self, saved, datetime.datetime.fromtimestamp(ts.st_mtime).strftime('%Y-%m-%d %H:%M:%S'))
                print(self, "Removing", saved)
                os.unlink(saved)

        if os.path.exists(saved):
            print(self, "Using", saved)
            with open(saved, 'rb') as f:
                return pickle.load(f)

        print(self, "No cache", saved)
        print(self, "Computing dates", saved)
        dates = []

        with tqdm(total=L2_DATES, desc='distance_dates') as bar:
            for i in range(0, L2_DATES):
                if (dm[:, i:i + 1] == np.inf).sum() == 0:
                    dates.append(i)
                bar.update(1)

        with open(saved, 'wb') as f:
            pickle.dump(dates, f)

        print(self, "Done", len(dates), saved)
        return dates


class ClusterMatrix(DistanceMatrix):

    def __init__(self,
                 field,
                 reference,
                 level,
                 readonly=False):

        self._level = level
        path = self.derived_path(reference._path, '.npy', 'cluster', level)
        self._reference = reference
        DistanceMatrix.__init__(self, field, path, reference, readonly)

    def populate(self, dm):
        from sklearn.cluster import DBSCAN

        print(self, 'populate', 'copy reference')
        dm[:] = self._reference.matrix

        epsilons = self._reference.unique_distances()
        # dates = self._reference.distance_dates()
        print('epsilons', epsilons)

        if self._level < 0:
            eps = self._field.cut_threshold
        else:
            eps = epsilons[self._level]

        print(self, 'populate', eps)
        scan = DBSCAN(eps=eps, min_samples=1, metric="precomputed").fit(self._reference.matrix)
        keep = set()
        seen = set()
        for i, lbl in enumerate(scan.labels_):
            assert lbl >= 0
            if lbl not in seen:
                keep.add(i)
                seen.add(lbl)

        skip = set(range(0, L2_DATES)).difference(keep)

        print("skip", len(skip), list(skip)[:10])
        for i in skip:
            dm[:, i:i + 1] = np.inf
            dm[i:i + 1, :] = np.inf
            dm[i, i] = 0

        print("done")

    def date_indexes(self):
        dm = self.matrix

        distance = self._path
        saved = self.derived_path(distance, '.pickle', 'dates')
        if os.path.exists(saved):
            ts = os.stat(saved)
            td = os.stat(distance)
            if td.st_mtime > ts.st_mtime:
                print(self, distance, datetime.datetime.fromtimestamp(td.st_mtime).strftime('%Y-%m-%d %H:%M:%S'))
                print(self, saved, datetime.datetime.fromtimestamp(ts.st_mtime).strftime('%Y-%m-%d %H:%M:%S'))
                print(self, "Removing", saved)
                os.unlink(saved)

        if os.path.exists(saved):
            print(self, "Using", saved)
            with open(saved, 'rb') as f:
                return pickle.load(f)

        print(self, "No cache", saved)
        print(self, "Computing dates", saved)
        dates = []

        with tqdm(total=L2_DATES, desc='distance_dates') as bar:
            for i in range(0, L2_DATES):
                if (dm[:, i:i + 1] == np.inf).sum() != L2_DATES - 1:
                    dates.append(i)
                bar.update(1)

        print('dates', len(dates))
        assert len(dates) > 1000

        with open(saved, 'wb') as f:
            pickle.dump(dates, f)

        print(self, "Done", len(dates), saved)
        return dates
