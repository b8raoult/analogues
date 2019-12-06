
from analogues.conf import cdsdb
from sqlalchemy import text
from gmpy2 import hamdist


class Method:

    def __init__(self, f):
        self.param = f.param
        self.domain = f.domain
        self.dataset = f.dataset
        self._sql_table = None
        self.name = repr(self)

        self.offset = f.minimum
        self.scale = f.maximum - f.minimum

    @property
    def to_path(self):
        return [self, self.alpha, self.scale, self.offset]

    def scaled(self, x):
        y = (x - self.offset) / self.scale
        assert y >= 0 and y <= 1, "%s %s %s" % (x, self.offset, self.scale)
        return y

    def hamming(self, s1, s2):
        assert s1 >= 0 and s1 <= 65535
        assert s2 >= 0 and s2 <= 65535

        result = hamdist(s1, s2) / 16.0
        assert result >= 0 and result <= 1.0
        return result

    def absdiff(self, r1, r2):
        result = abs(self.scaled(r1) - self.scaled(r2))
        assert result >= 0 and result <= 1.0, 'result=%s r1=%s r2=%s' % (result, self.scaled(r1), self.scaled(r2))
        return result

    def initialise(self):
        pass

    @property
    def n(self):
        return int(repr(self)[len('Method'):])

    def __repr__(self):
        return self.__class__.__name__.split('.')[-1].lower()

    @property
    def sql_table(self):
        if self._sql_table is None:
            self._sql_table = 'methods'

            STMT = text("""
                CREATE TABLE IF NOT EXISTS {table} (
                      name    VARCHAR(255),
                      param   VARCHAR(255),
                      domain  VARCHAR(255),
                      dataset VARCHAR(255),
                      alpha   REAL,
                      score   REAL,
                      seed    REAL,
                      CONSTRAINT {table}_inx UNIQUE (name, param, domain, dataset)
                );
                """.format(table=self._sql_table))

            with cdsdb.begin() as connection:
                connection.execute(STMT)

            try:
                with cdsdb.begin() as connection:
                    pass
            except Exception as e:
                print(e)

        return self._sql_table

    @property
    def alpha(self):
        GET_ALPHA = text("""
              SELECT alpha FROM {table}
              where name=:name
              and param=:param
              and domain=:domain
              and dataset=:dataset""".format(table=self.sql_table))
        with cdsdb.begin() as connection:
            result = connection.execute(GET_ALPHA,
                                        name=self.name,
                                        param=self.param,
                                        domain=self.domain,
                                        dataset=self.dataset).scalar()
            if result is None:
                result = 0.5
        return result

    @alpha.setter
    def alpha(self, alpha):
        SET_ALPHA = text("""
            INSERT INTO {table} (name, param, domain, dataset, alpha)
            VALUES (:name, :param, :domain, :dataset, :alpha)
            ON CONFLICT (name, param, domain, dataset)
            DO UPDATE SET alpha=:alpha
            """.format(table=self.sql_table))

        with cdsdb.begin() as connection:
            connection.execute(SET_ALPHA,
                               name=self.name,
                               param=self.param,
                               domain=self.domain,
                               dataset=self.dataset,
                               alpha=alpha)

    @property
    def seed(self):
        GET_SEED = text("""
            SELECT seed FROM {table}
            where name=:name
            and param=:param
            and domain=:domain
            and dataset=:dataset""".format(table=self.sql_table))
        with cdsdb.begin() as connection:
            result = connection.execute(GET_SEED,
                                        name=self.name,
                                        param=self.param,
                                        domain=self.domain,
                                        dataset=self.dataset).scalar()
            if result is None:
                result = 0.5
        return result

    @seed.setter
    def seed(self, seed):
        SET_SEED = text("""
            INSERT INTO {table} (name, param, domain, dataset, seed)
            VALUES (:name, :param, :domain, :dataset, :seed)
            ON CONFLICT (name, param, domain, dataset)
            DO UPDATE SET seed=:seed
            """.format(table=self.sql_table))

        with cdsdb.begin() as connection:
            connection.execute(SET_SEED,
                               name=self.name,
                               param=self.param,
                               domain=self.domain,
                               dataset=self.dataset,
                               seed=seed)

    @property
    def score(self):
        GET_ALPHA = text("""
            SELECT score FROM {table}
            where name=:name
            and param=:param
            and domain=:domain
            and dataset=:dataset""".format(table=self.sql_table))
        with cdsdb.begin() as connection:
            result = connection.execute(GET_ALPHA,
                                        name=self.name,
                                        param=self.param,
                                        domain=self.domain,
                                        dataset=self.dataset).scalar()
            if result is None:
                result = 0.5
        return result

    @score.setter
    def score(self, score):
        SET_ALPHA = text("""
            INSERT INTO {table} (name, param, domain, dataset, score)
            VALUES (:name, :param, :domain, :dataset, :score)
            ON CONFLICT (name, param, domain, dataset)
            DO UPDATE SET score=:score
            """.format(table=self.sql_table))

        with cdsdb.begin() as connection:
            connection.execute(SET_ALPHA,
                               name=self.name,
                               param=self.param,
                               domain=self.domain,
                               dataset=self.dataset,
                               score=score)


class Method10(Method):

    def fingerprint_distance(self, r1, s1, r2, s2, alpha):
        return self.hamming(s1, s2)


class Method11(Method):

    def fingerprint_distance(self, r1, s1, r2, s2, alpha):
        return self.absdiff(r1, r2)
