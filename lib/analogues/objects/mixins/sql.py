from sqlalchemy import text
from analogues.conf import cdsdb
from grib import GribFile
import numpy as np
from analogues.fingerprint import FingerPrint


class FieldSQL:

    def __init__(self):
        self._fingerprint_table = None
        self._file_table = None

        self._sql_dates = None

        self._minimum = None
        self._maximum = None
        self._mean = None
        self._stddev = None

        self._smoothness1_maximum = None
        self._smoothness1_average = None
        self._smoothness1_average_no_constants = None

        self._smoothness2_maximum = None
        self._smoothness2_average = None

        self.update_missing_sql_fields()

        self._SELECT_SAMPLE = None
        self._SELECT_FIRST_SAMPLE = None

    def seed(self, valid_dates):

        insert = text("""
            INSERT INTO {table} (valid_date) VALUES (:valid_date)
            ON CONFLICT DO NOTHING;
        """.format(table=self.fingerprint_table))

        with cdsdb.begin() as connection:

            for valid_date in valid_dates:
                connection.execute(insert, valid_date=valid_date)

    @property
    def fingerprint_table(self):
        if self._fingerprint_table is None:
            self._fingerprint_table = "fingerprint_{param}_{domain}_{dataset}".format(param=self.param,
                                                                                      domain=self.domain,
                                                                                      dataset=self.dataset)

            STMT = text("""
                CREATE TABLE IF NOT EXISTS {table} (
                    valid_date        TIMESTAMP NOT NULL UNIQUE,

                    -- Fingerprint
                    fingerprint_s          INTEGER , -- should be smallint, but smallint is signed
                    fingerprint_r          REAL    , -- mean

                    field_min REAL,
                    field_max REAL,
                    -- FILE

                    file_id           INTEGER, -- REFERENCES files(id),
                    position          BIGINT,

                    -- Updated
                    updated           TIMESTAMP NOT NULL DEFAULT ({now})
                );
                """.format(table=self._fingerprint_table,
                           now=cdsdb.sql_now))
            with cdsdb.begin() as connection:
                connection.execute(STMT)

            # for col in ('field_min', 'field_max'):
            #     try:
            #         with cdsdb.begin() as connection:
            #             alter = "alter table {table} add column {col} real".format(table=self._fingerprint_table, col=col)
            #             connection.execute(text(alter))
            #     except Exception as e:
            #         print(e)
            #         pass

        return self._fingerprint_table

    @property
    def file_table(self):
        if self._file_table is None:
            self._file_table = "file_{param}_{domain}_{dataset}".format(param=self.param,
                                                                        domain=self.domain,
                                                                        dataset=self.dataset)

            STMT = text("""
                CREATE TABLE IF NOT EXISTS {table} (
                    id   {increment},
                    path TEXT UNIQUE NOT NULL --CHECK (path <> '')
                );
                """.format(table=self._file_table,
                           increment=cdsdb.sql_autoincrement))
            with cdsdb.begin() as connection:
                connection.execute(STMT)

        return self._file_table

    def fingerprints(self):

        STMT = text("""
            SELECT valid_date, fingerprint_r, fingerprint_s FROM {table}
            WHERE fingerprint_r IS NOT NULL
            AND fingerprint_s IS NOT NULL
            AND file_id IS NOT NULL
            """.format(table=self.fingerprint_table))

        with cdsdb.begin() as connection:
            result = connection.execute(STMT)
            return dict((cdsdb.sql_to_datetime(d[0]), (d[1], d[2])) for d in result)

    @property
    def SELECT_SAMPLE(self):
        if self._SELECT_SAMPLE is None:
            self._SELECT_SAMPLE = text("""
             SELECT path, position FROM {file_table}, {fingerprint_table}
             WHERE {file_table}.id = {fingerprint_table}.file_id
             AND valid_date=:valid_date
            """.format(file_table=self.file_table, fingerprint_table=self.fingerprint_table))
        return self._SELECT_SAMPLE

    @property
    def SELECT_FIRST_SAMPLE(self):
        if self._SELECT_FIRST_SAMPLE is None:
            self._SELECT_FIRST_SAMPLE = text("""
             SELECT path, position FROM {file_table}, {fingerprint_table}
            WHERE {file_table}.id = {fingerprint_table}.file_id AND fingerprint_r = (
            SELECT MAX(fingerprint_r) FROM {fingerprint_table}
                WHERE file_id IS NOT NULL)
            """.format(file_table=self.file_table, fingerprint_table=self.fingerprint_table))
        return self._SELECT_FIRST_SAMPLE

    @property
    def max_fingerprint_distance(self):
        if self._max_fingerprint_distance is None:
            GET_ALPHA = text("SELECT max_fingerprint_distance FROM alpha where param=:param and domain=:domain and dataset=:dataset")
            with cdsdb.begin() as connection:
                self._max_fingerprint_distance = connection.execute(GET_ALPHA,
                                                                    param=self.param,
                                                                    domain=self.domain,
                                                                    dataset=self.dataset).scalar()
                if self._max_fingerprint_distance is None:
                    self._max_fingerprint_distance = 0.0
        return self._max_fingerprint_distance

    @max_fingerprint_distance.setter
    def max_fingerprint_distance(self, max_fingerprint_distance):
        self._max_fingerprint_distance = max_fingerprint_distance
        SET_ALPHA = text("""
            INSERT INTO alpha (param, domain, dataset, max_fingerprint_distance)
            VALUES (:param, :domain, :dataset, :max_fingerprint_distance)
            ON CONFLICT (param, domain, dataset)
            DO UPDATE SET max_fingerprint_distance=:max_fingerprint_distance
            """)

        with cdsdb.begin() as connection:
            connection.execute(SET_ALPHA,
                               param=self.param,
                               domain=self.domain,
                               dataset=self.dataset,
                               max_fingerprint_distance=max_fingerprint_distance)
        return self._max_fingerprint_distance

    ########################################################################

    @property
    def smoothness1_maximum(self):
        if self._smoothness1_maximum is None:
            GET_MINIMUM = text("SELECT smoothness1_maximum FROM alpha where param=:param and domain=:domain and dataset=:dataset")
            with cdsdb.begin() as connection:
                self._smoothness1_maximum = connection.execute(GET_MINIMUM,
                                                               param=self.param,
                                                               domain=self.domain,
                                                               dataset=self.dataset).scalar()
                if self._smoothness1_maximum is None:
                    self._smoothness1_maximum = 0.0
        return self._smoothness1_maximum

    @smoothness1_maximum.setter
    def smoothness1_maximum(self, smoothness1_maximum):
        self._smoothness1_maximum = smoothness1_maximum
        SET_MINIMUM = text("""
            INSERT INTO alpha (param, domain, dataset, smoothness1_maximum)
            VALUES (:param, :domain, :dataset, :smoothness1_maximum)
            ON CONFLICT (param, domain, dataset)
            DO UPDATE SET smoothness1_maximum=:smoothness1_maximum
            """)

        with cdsdb.begin() as connection:
            connection.execute(SET_MINIMUM,
                               param=self.param,
                               domain=self.domain,
                               dataset=self.dataset,
                               smoothness1_maximum=smoothness1_maximum)
        return self._smoothness1_maximum

    @property
    def smoothness1_average(self):
        if self._smoothness1_average is None:
            GET_MINIMUM = text("SELECT smoothness1_average FROM alpha where param=:param and domain=:domain and dataset=:dataset")
            with cdsdb.begin() as connection:
                self._smoothness1_average = connection.execute(GET_MINIMUM,
                                                               param=self.param,
                                                               domain=self.domain,
                                                               dataset=self.dataset).scalar()
                if self._smoothness1_average is None:
                    self._smoothness1_average = 0.0
        return self._smoothness1_average

    @smoothness1_average.setter
    def smoothness1_average(self, smoothness1_average):
        self._smoothness1_average = smoothness1_average
        SET_MINIMUM = text("""
            INSERT INTO alpha (param, domain, dataset, smoothness1_average)
            VALUES (:param, :domain, :dataset, :smoothness1_average)
            ON CONFLICT (param, domain, dataset)
            DO UPDATE SET smoothness1_average=:smoothness1_average
            """)

        with cdsdb.begin() as connection:
            connection.execute(SET_MINIMUM,
                               param=self.param,
                               domain=self.domain,
                               dataset=self.dataset,
                               smoothness1_average=smoothness1_average)
        return self._smoothness1_average

    @property
    def smoothness1_average_no_constants(self):
        if self._smoothness1_average_no_constants is None:
            GET_MINIMUM = text("SELECT smoothness1_average_no_constants FROM alpha where param=:param and domain=:domain and dataset=:dataset")
            with cdsdb.begin() as connection:
                self._smoothness1_average_no_constants = connection.execute(GET_MINIMUM,
                                                                            param=self.param,
                                                                            domain=self.domain,
                                                                            dataset=self.dataset).scalar()
                if self._smoothness1_average_no_constants is None:
                    self._smoothness1_average_no_constants = 0.0
        return self._smoothness1_average_no_constants

    @smoothness1_average_no_constants.setter
    def smoothness1_average_no_constants(self, smoothness1_average_no_constants):
        self._smoothness1_average_no_constants = smoothness1_average_no_constants
        SET_MINIMUM = text("""
            INSERT INTO alpha (param, domain, dataset, smoothness1_average_no_constants)
            VALUES (:param, :domain, :dataset, :smoothness1_average_no_constants)
            ON CONFLICT (param, domain, dataset)
            DO UPDATE SET smoothness1_average_no_constants=:smoothness1_average_no_constants
            """)

        with cdsdb.begin() as connection:
            connection.execute(SET_MINIMUM,
                               param=self.param,
                               domain=self.domain,
                               dataset=self.dataset,
                               smoothness1_average_no_constants=smoothness1_average_no_constants)
        return self._smoothness1_average_no_constants

    ########################################################################

    @property
    def smoothness2_maximum(self):
        if self._smoothness2_maximum is None:
            GET_MINIMUM = text("SELECT smoothness2_maximum FROM alpha where param=:param and domain=:domain and dataset=:dataset")
            with cdsdb.begin() as connection:
                self._smoothness2_maximum = connection.execute(GET_MINIMUM,
                                                               param=self.param,
                                                               domain=self.domain,
                                                               dataset=self.dataset).scalar()
                if self._smoothness2_maximum is None:
                    self._smoothness2_maximum = 0.0
        return self._smoothness2_maximum

    @smoothness2_maximum.setter
    def smoothness2_maximum(self, smoothness2_maximum):
        self._smoothness2_maximum = smoothness2_maximum
        SET_MINIMUM = text("""
            INSERT INTO alpha (param, domain, dataset, smoothness2_maximum)
            VALUES (:param, :domain, :dataset, :smoothness2_maximum)
            ON CONFLICT (param, domain, dataset)
            DO UPDATE SET smoothness2_maximum=:smoothness2_maximum
            """)

        with cdsdb.begin() as connection:
            connection.execute(SET_MINIMUM,
                               param=self.param,
                               domain=self.domain,
                               dataset=self.dataset,
                               smoothness2_maximum=smoothness2_maximum)
        return self._smoothness2_maximum

    @property
    def smoothness2_average(self):
        if self._smoothness2_average is None:
            GET_MINIMUM = text("SELECT smoothness2_average FROM alpha where param=:param and domain=:domain and dataset=:dataset")
            with cdsdb.begin() as connection:
                self._smoothness2_average = connection.execute(GET_MINIMUM,
                                                               param=self.param,
                                                               domain=self.domain,
                                                               dataset=self.dataset).scalar()
                if self._smoothness2_average is None:
                    self._smoothness2_average = 0.0
        return self._smoothness2_average

    @smoothness2_average.setter
    def smoothness2_average(self, smoothness2_average):
        self._smoothness2_average = smoothness2_average
        SET_MINIMUM = text("""
            INSERT INTO alpha (param, domain, dataset, smoothness2_average)
            VALUES (:param, :domain, :dataset, :smoothness2_average)
            ON CONFLICT (param, domain, dataset)
            DO UPDATE SET smoothness2_average=:smoothness2_average
            """)

        with cdsdb.begin() as connection:
            connection.execute(SET_MINIMUM,
                               param=self.param,
                               domain=self.domain,
                               dataset=self.dataset,
                               smoothness2_average=smoothness2_average)
        return self._smoothness2_average

    @property
    def smoothness2_average_no_constants(self):
        if self._smoothness2_average_no_constants is None:
            GET_MINIMUM = text("SELECT smoothness2_average_no_constants FROM alpha where param=:param and domain=:domain and dataset=:dataset")
            with cdsdb.begin() as connection:
                self._smoothness2_average_no_constants = connection.execute(GET_MINIMUM,
                                                                            param=self.param,
                                                                            domain=self.domain,
                                                                            dataset=self.dataset).scalar()
                if self._smoothness2_average_no_constants is None:
                    self._smoothness2_average_no_constants = 0.0
        return self._smoothness2_average_no_constants

    @smoothness2_average_no_constants.setter
    def smoothness2_average_no_constants(self, smoothness2_average_no_constants):
        self._smoothness2_average_no_constants = smoothness2_average_no_constants
        SET_MINIMUM = text("""
            INSERT INTO alpha (param, domain, dataset, smoothness2_average_no_constants)
            VALUES (:param, :domain, :dataset, :smoothness2_average_no_constants)
            ON CONFLICT (param, domain, dataset)
            DO UPDATE SET smoothness2_average_no_constants=:smoothness2_average_no_constants
            """)

        with cdsdb.begin() as connection:
            connection.execute(SET_MINIMUM,
                               param=self.param,
                               domain=self.domain,
                               dataset=self.dataset,
                               smoothness2_average_no_constants=smoothness2_average_no_constants)
        return self._smoothness2_average_no_constants

    ########################################################################

    @property
    def minimum(self):
        if self._minimum is None:
            GET_MINIMUM = text("SELECT minimum FROM alpha where param=:param and domain=:domain and dataset=:dataset")
            with cdsdb.begin() as connection:
                self._minimum = connection.execute(GET_MINIMUM,
                                                   param=self.param,
                                                   domain=self.domain,
                                                   dataset=self.dataset).scalar()
                if self._minimum is None:
                    self._minimum = 0.0
        return self._minimum

    @minimum.setter
    def minimum(self, minimum):
        self._minimum = minimum
        SET_MINIMUM = text("""
            INSERT INTO alpha (param, domain, dataset, minimum)
            VALUES (:param, :domain, :dataset, :minimum)
            ON CONFLICT (param, domain, dataset)
            DO UPDATE SET minimum=:minimum
            """)

        with cdsdb.begin() as connection:
            connection.execute(SET_MINIMUM,
                               param=self.param,
                               domain=self.domain,
                               dataset=self.dataset,
                               minimum=minimum)
        return self._minimum

    @property
    def maximum(self):
        if self._maximum is None:
            GET_MAXIMUM = text("SELECT maximum FROM alpha where param=:param and domain=:domain and dataset=:dataset")
            with cdsdb.begin() as connection:
                self._maximum = connection.execute(GET_MAXIMUM,
                                                   param=self.param,
                                                   domain=self.domain,
                                                   dataset=self.dataset).scalar()
                if self._maximum is None:
                    self._maximum = 0.0
        return self._maximum

    @maximum.setter
    def maximum(self, maximum):
        self._maximum = maximum
        SET_MAXIMUM = text("""
            INSERT INTO alpha (param, domain, dataset, maximum)
            VALUES (:param, :domain, :dataset, :maximum)
            ON CONFLICT (param, domain, dataset)
            DO UPDATE SET maximum=:maximum
            """)

        with cdsdb.begin() as connection:
            connection.execute(SET_MAXIMUM,
                               param=self.param,
                               domain=self.domain,
                               dataset=self.dataset,
                               maximum=maximum)
        return self._maximum

    @property
    def mean(self):
        if self._mean is None:
            GET_MEAN = text("SELECT mean FROM alpha where param=:param and domain=:domain and dataset=:dataset")
            with cdsdb.begin() as connection:
                self._mean = connection.execute(GET_MEAN,
                                                param=self.param,
                                                domain=self.domain,
                                                dataset=self.dataset).scalar()
                if self._mean is None:
                    self._mean = 0.0
        return self._mean

    @mean.setter
    def mean(self, mean):
        self._mean = mean
        SET_MEAN = text("""
            INSERT INTO alpha (param, domain, dataset, mean)
            VALUES (:param, :domain, :dataset, :mean)
            ON CONFLICT (param, domain, dataset)
            DO UPDATE SET mean=:mean
            """)

        with cdsdb.begin() as connection:
            connection.execute(SET_MEAN,
                               param=self.param,
                               domain=self.domain,
                               dataset=self.dataset,
                               mean=mean)
        return self._mean

    @property
    def stddev(self):
        if self._stddev is None:
            GET_STDDEV = text("SELECT stddev FROM alpha where param=:param and domain=:domain and dataset=:dataset")
            with cdsdb.begin() as connection:
                self._stddev = connection.execute(GET_STDDEV,
                                                  param=self.param,
                                                  domain=self.domain,
                                                  dataset=self.dataset).scalar()
                if self._stddev is None:
                    self._stddev = 0.0
        return self._stddev

    @stddev.setter
    def stddev(self, stddev):
        self._stddev = stddev
        SET_STDDEV = text("""
            INSERT INTO alpha (param, domain, dataset, stddev)
            VALUES (:param, :domain, :dataset, :stddev)
            ON CONFLICT (param, domain, dataset)
            DO UPDATE SET stddev=:stddev
            """)

        with cdsdb.begin() as connection:
            connection.execute(SET_STDDEV,
                               param=self.param,
                               domain=self.domain,
                               dataset=self.dataset,
                               stddev=stddev)
        return self._stddev

    def update_missing_sql_fields(self):

        select = text("""
        SELECT valid_date FROM {table}
        WHERE file_id IS NOT NULL
        AND (field_max IS NULL OR field_min IS NULL)
        """.format(table=self.fingerprint_table))

        update = text("""
        UPDATE {table}
        SET field_max    = :field_max,
            field_min    = :field_min
        WHERE valid_date = :valid_date
        """.format(table=self.fingerprint_table))

        with cdsdb.begin() as connection:

            result = connection.execute(select)
            dates = [cdsdb.sql_to_datetime(x[0]) for x in result]

        count = 0

        for d in dates:
            count += 1
            values = self.array(d)

            # print('Update', d)
            with cdsdb.begin() as connection:
                connection.execute(update, field_max=np.amax(values), field_min=np.amin(values), valid_date=d)

        if count:
            print('update_missing_sql_fields', count)

    def index_grib_file(self, target):
        insert_files = text("""
        INSERT INTO {table} (path) VALUES (:path)
        --ON CONFLICT (path) DO NOTHING -- 9.5
        """.format(table=self.file_table))

        select_file_id = text("""
        SELECT id FROM {table} WHERE path=:path
        """.format(table=self.file_table))

        # query_7 = text("""
        # update {table}
        #   set file_id       = :file_id,
        #       position      = :position,
        #       fingerprint_r = :fingerprint_r,
        #       fingerprint_s = :fingerprint_s
        # where valid_date = :valid_date
        # """.format(table=self.fingerprint_table))

        query_7 = text("""
        INSERT INTO {table} (file_id,
                             position,
                             fingerprint_r,
                             fingerprint_s,
                             field_max,
                             field_min,
                             valid_date)
        VALUES(:file_id, :position, :fingerprint_r, :fingerprint_s, :field_max, :field_min, :valid_date)
        ON CONFLICT(valid_date) DO UPDATE
        SET file_id         = :file_id,
              position      = :position,
              fingerprint_r = :fingerprint_r,
              fingerprint_s = :fingerprint_s,
              field_max     = :field_max,
              field_min     = :field_min
        """.format(table=self.fingerprint_table))

        n = 0
        with cdsdb.begin() as connection:
            connection.execute(insert_files, path=target)
            fileid = connection.execute(select_file_id,
                                        path=target).scalar()
            assert fileid is not None

            for g in GribFile(target):

                d = dict(file_id=fileid,
                         valid_date=g.valid_date,
                         position=int(g.offset))

                finger = FingerPrint(g.array,
                                     depth=3)

                finger.to_db(d)
                # print(query_7)
                d['field_max'] = np.amax(g.array)
                d['field_min'] = np.amin(g.array)
                # print(d)

                connection.execute(query_7, **d)
                n += 1

        print(self, 'added', n, 'field(s)')

    @property
    def sql_dates(self):

        if self._sql_dates is None:

            STMT = text("""
            SELECT valid_date FROM {table}
            WHERE file_id IS NOT NULL
            ORDER BY valid_date
            """.format(table=self.fingerprint_table))

            with cdsdb.begin() as connection:
                result = connection.execute(STMT)
                self._sql_dates = [cdsdb.sql_to_datetime(x[0]) for x in result]
        return self._sql_dates
