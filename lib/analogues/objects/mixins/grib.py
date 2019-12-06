import os

from lru import LRU
from analogues.conf import cdsdb
from grib import GribFile
from analogues.objects.params import Param
from analogues.objects.domains import Domain
from analogues.objects.datasets import Dataset
from analogues.conf import ROOT, CACHE
import time
import dateutil.parser
import datetime


class FieldGrib:

    def __init__(self):
        self._gribs = LRU(10)

    def grib_path_offset(self, date):
        with cdsdb.begin() as connection:

            date = cdsdb.sql_to_datetime(date)

            # print(self.SELECT_SAMPLE, date)
            result = connection.execute(self.SELECT_SAMPLE, valid_date=date)

            for path, offset in result:
                if os.path.exists(path):
                    return (path, offset)
                else:
                    print(path, 'does not exists')

        print('Not found', self, date)

        return self.retrieve(date)

    def grib(self, date):
        if date not in self._gribs:
            (path, offset) = self.grib_path_offset(date)
            self._gribs[date] = GribFile(path).at_offset(offset)
        return self._gribs[date]

    def array(self, date):
        return self.grib(date).array

    def retrieve(self, date):

        if isinstance(date, str):
            date = dateutil.parser.parse(date)

        retriever = Param.lookup(self.param).retriever(cdsdb)
        retriever.domain(Domain.lookup(self.domain))
        retriever.dataset(Dataset.lookup(self.dataset))

        dates = set()
        times = set()

        dates.add(date.strftime('%Y%m%d'))
        times.add(date.strftime('%H%M'))

        retriever.dates(list(dates))
        retriever.times(list(times))

        target = os.path.join(CACHE, "%s-%s-%s-%s-%s.grib" % (self.param,
                                                              self.domain,
                                                              self.dataset,
                                                              date.isoformat(),
                                                              time.time()))

        retriever.execute(target)
        assert os.path.getsize(target) > 0

        self.index_grib_file(target)

        return (target, 0)

    def sample(self, date=None):

        if date is not None:
            return self.grib(date)

        with cdsdb.begin() as connection:

            result = connection.execute(self.SELECT_FIRST_SAMPLE,
                                        valid_date=date)
            for path, offset in result:
                if os.path.exists(path):
                    return GribFile(path).at_offset(offset)

        return self.grib(datetime.date(2000, 1, 1))
