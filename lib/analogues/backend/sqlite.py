from sqlalchemy import create_engine, text


# import logging

# logging.basicConfig()
# logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)

import datetime

from .base import EngineBase
from ..retriever import api_retriever


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
  CONSTRAINT alpha_inx UNIQUE (param, domain, dataset)
);
""",

"""
ALTER TABLE alpha ADD COLUMN alpha_scaled REAL;
ALTER TABLE alpha ADD COLUMN max_fingerprint_distance REAL;

"""


]


PATH = '/Users/baudouin/git/analogues/sqlite-hamming/hamming'


class SqliteEngine(EngineBase):

    sql_now = 'CURRENT_TIMESTAMP'
    sql_autoincrement = 'INTEGER PRIMARY KEY AUTOINCREMENT'

    engine = create_engine('sqlite://///Users/baudouin/Dropbox/phd/data/analogues.db')

    simple_retriever = api_retriever.SimpleRetriever
    wind_retriever = api_retriever.WindRetriever
    log_retriever = api_retriever.LogRetriever
    gauss_retriever = api_retriever.GaussRetriever
    exp_retriever = api_retriever.ExpRetriever
    # def __init__(self):

    #     print('==========', self.engine.connect)
    #     self.engine.connect = wrap_connect(self.engine.connect)
    #     print('==========', self.engine.connect)

    # connection = self.engine.connect()
    # connection.connection.enable_load_extension(True)
    #
    # connection.connection.execute("SELECT load_extension('%s', 'hamming_load');" % (path,))

    #                        path='/Users/baudouin/git/analogues/sqlite-hamming/hamming',
    #                        func='hamming_load')

    def begin(self):
        txn = super().begin()
        txn.conn.connection.enable_load_extension(True)
        txn.conn.execute("SELECT load_extension('%s', 'hamming_load');" % (PATH,))
        return txn

    def initdb(self):
        # logging.basicConfig()
        # logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)
        with self.begin() as connection:
            for s in STATEMENTS:
                try:
                    connection.execute(text(s))
                except Exception as e:
                    print(e)

    def sql_date_to_yyyymmdd(self, date):
        return date.split(' ')[0]

    def sql_date_to_hhmm(self, date):
        return date.split(' ')[1][:5]

    def sql_to_datetime(self, date):
        if isinstance(date, datetime.datetime):
            return date
        return datetime.datetime.fromisoformat(date)

    def sql_in_statement(self, name, values):
        names = ['%s_%d' % (name, i) for i, _ in enumerate(values)]
        d = dict((k, v) for k, v in zip(names, values))
        return "(:%s)" % (',:'.join(names)), d
