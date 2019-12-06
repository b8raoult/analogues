from sqlalchemy import create_engine, text
import subprocess
import os
# import logging

from .base import EngineBase
from ..retriever import mars_retriever


STATEMENTS = [

    """
CREATE TABLE IF NOT EXISTS alpha (
  param        VARCHAR(255),
  domain       VARCHAR(255),
  dataset      VARCHAR(255),
  alpha        REAL,
  alpha_scaled REAL,
  minimum      REAL,
  maximum      REAL,
  mean         REAL,
 max_fingerprint_distance REAL,
  CONSTRAINT alpha_inx UNIQUE (param, domain, dataset)
);
""",

#     """
# ALTER TABLE alpha ADD COLUMN alpha_scaled REAL;
# ALTER TABLE alpha ADD COLUMN max_fingerprint_distance REAL;

# """,

# """


# ALTER TABLE alpha ADD COLUMN smoothness1_maximum REAL;
# ALTER TABLE alpha ADD COLUMN smoothness1_average REAL;
# ALTER TABLE alpha ADD COLUMN smoothness1_average_no_constants REAL;

# ALTER TABLE alpha ADD COLUMN smoothness2_maximum REAL;
# ALTER TABLE alpha ADD COLUMN smoothness2_average REAL;
# ALTER TABLE alpha ADD COLUMN smoothness2_average_no_constants REAL;


# """
"""
ALTER TABLE alpha ADD COLUMN stdev REAL;
"""


]


class PostgresEngine(EngineBase):

    engine = create_engine('postgresql://cdsuser@analogues:5432/analogues')

    simple_retriever = mars_retriever.SimpleRetriever
    wind_retriever = mars_retriever.WindRetriever
    log_retriever = mars_retriever.LogRetriever
    gauss_retriever = mars_retriever.GaussRetriever
    exp_retriever = mars_retriever.ExpRetriever

    sql_now = 'now()'
    sql_autoincrement = 'SERIAL'

    def initdb(self):
        # logging.basicConfig()
        # logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)
        for s in STATEMENTS:
            try:
                with self.begin() as connection:
                    connection.execute(text(s))
            except Exception as e:
                print(e)

    def sql_date_to_yyyymmdd(self, date):
        return date.strftime('%Y%m%d')

    def sql_date_to_hhmm(self, date):
        return date.strftime('%H%M')

    def sql_to_datetime(self, date):
        return date

    def get_mars_data(self, requests, target):
        mars_r = "%s.mars" % (target,)
        with open(mars_r, "w") as f:

            for r in requests:
                if r:
                    req = [r.get("_verb", "retrieve")]
                    for k, v in r.items():
                        if not k.startswith('_'):
                            if not isinstance(v, list):
                                v = [v]
                            req.append("%s=%s" % (k, '/'.join(v)))

                    print(",\n     ".join(req), file=f)

            print(",target='%s'" % (target,), file=f)

        assert subprocess.call(['mars', mars_r]) == 0
        os.unlink(mars_r)

    def sql_in_statement(self, name, values):
        return ":%s" % (name,), {name: tuple(values)}
