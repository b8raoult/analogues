import sqlite3
import os

from analogues.fingerprint import FingerPrint, FingerPrintFromDB
import traceback
from analogues import conf
import errno


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


class DB(object):

    def __init__(self, param, depth, wavelet, mode, domain, readonly=True):
        self.param = param
        self.depth = depth
        self.wavelet = wavelet
        self.mode = mode
        self.path = conf.fingerprints_db(wavelet=wavelet, mode=mode, param=param, depth=depth, domain=domain)
        self._con = None
        self._cursor = None
        self.readonly = readonly
        print("DB-PATH", self.path)

    def __repr__(self):
        return self.path

    def close(self):
        if self._con:
            self._con.close()
        self._con = None
        self._cursor = None

    @property
    def con(self):
        if self._con is None:
            if self.readonly:
                if not os.path.exists(self.path):
                    raise Exception("%s does not exists" % (self.path,))
            mkdir_p(os.path.dirname(self.path))
            self._con = sqlite3.connect(self.path, detect_types=sqlite3.PARSE_DECLTYPES)
        return self._con

    @property
    def cursor(self):
        if self._cursor is None:
            self._cursor = self.con.cursor()
        return self._cursor

    def create(self, gribs, bar=None, force=False):
        print(self.path)
        if os.path.exists(self.path):
            if force:
                print("unlink", self.path)
                os.unlink(self.path)
            else:
                count = self.cursor.execute("select count(*) from fingerprints").fetchone()[0]
                print("count = ", count)
                if count > 0:
                    assert count == len(gribs)
                    return

        c = self.cursor
        # c.execute("drop table fingerprints")
        c.execute("create table if not exists fingerprints ([date] date, fingerprint blob, offset long)")
        c.execute("delete from fingerprints")

        for g in gribs:
            try:
                f = FingerPrint(g.array, depth=self.depth, wavelet=self.wavelet, mode=self.mode)
                row = [g.valid_date, sqlite3.Binary(f.encode()), g.offset]
            except Exception as e:
                print(e)
                traceback.print_exc()
                print("unlink", self.path)
                os.unlink(self.path)
                return

            c.execute("insert into fingerprints values(?,?,?)", row)
            if bar:
                bar.next(g.totalLength)

        self.con.commit()
        c.execute("create index dateidx on fingerprints(date)")
        if bar:
            bar.finish()

    @property
    def dates(self):
        # return list(d[0]
        for d in self.cursor.execute("select date from fingerprints"):
            yield d[0]

    @property
    def entries(self):
        for d in self.cursor.execute("select date, fingerprint from fingerprints"):
            yield (d[0], FingerPrintFromDB(d[1], self.mode))
        # return list((d[0], FingerPrintFromDB(d[1], d[2])) )

    def offset(self, date):
        return self.cursor.execute("select offset from fingerprints where date=%s" % (date,)).fetchone()[0]

    def fingerprint(self, date):
        d = self.cursor.execute("select fingerprint from fingerprints where date=%s" % (date,)).fetchone()
        return FingerPrintFromDB(d[0], self.mode)
