import os

from sqlalchemy import text
from analogues.conf import cdsdb
from analogues import Domain, Param, Dataset, Field
from analogues import DEFAULT_DATASET, DEFAULT_DOMAIN

import random


def do_initdb(args):
    cdsdb.initdb()


def mars_request_for_missing_fields(args):

    assert args.param
    assert args.target

    f = Field(args.param)

    query_0 = text("""
    select * from {table} ;
    """.format(table=f.file_table))

    query_10 = text("""
    update {table} set file_id=null where file_id=:file_id;
    """.format(table=f.fingerprint_table))

    query_11 = text("""
    delete from {table} where id=:file_id;
    """.format(table=f.file_table))

    missing = set()
    with cdsdb.begin() as connection:
        for e in connection.execute(query_0):
            if not os.path.exists(e[1]):
                print("MISSING file %s" % (e[1],))
                missing.add(e[0])

    if missing:
        print("CLEANUP MISSING:", len(missing))
        missing = list(missing)[:500]
        with cdsdb.begin() as connection:
            for m in missing:
                connection.execute(query_10, file_id=m)
                connection.execute(query_11, file_id=m)
        print("CLEANUP MISSING:", len(missing))

    args.target = os.path.realpath(args.target)

    query_2 = text("""
    select valid_date from {table} where file_id is null
    order by updated limit :limit;
    """.format(table=f.fingerprint_table))

    retriever = Param.lookup(f.param).retriever(cdsdb)
    retriever.domain(Domain.lookup(f.domain))
    retriever.dataset(Dataset.lookup(f.dataset))

    dates = set()
    times = set()
    valid_dates = []

    with cdsdb.begin() as connection:

        for valid_date in connection.execute(query_2, limit=366):
            d = valid_date[0]
            dates.add(cdsdb.sql_date_to_yyyymmdd(d))
            times.add(cdsdb.sql_date_to_hhmm(d))
            valid_dates.append(d)

    # dates = list(dates)[:400]
    # times = ['12']

    retriever.dates(list(dates))
    retriever.times(list(times))

    retriever.execute(args.target)

    if not os.path.exists(args.target):
        print("%s does not exists, skipped" % (args.target,))
    else:
        f.index_grib_file(args.target)

    insql, vals = cdsdb.sql_in_statement('valid_dates', valid_dates)

    query_6 = text("""
            update {table}
              set updated={now}
            where valid_date in {insql};
        """.format(table=f.fingerprint_table,
                   now=cdsdb.sql_now,
                   insql=insql))
    # print(query_6)
    with cdsdb.begin() as connection:
        connection.execute(query_6, **vals)


def do_index(args):
    f = Field(args.param)
    args.target = os.path.realpath(args.target)
    print('index', f, args.target)

    if not os.path.exists(args.target):
        print("%s does not exists, skipped" % (args.target,))
    else:
        f.index_grib_file(args.target)


def do_seed(args):
    from datetime import datetime
    from dateutil.rrule import rrule, DAILY

    f = Field(args.param, args.domain, args.dataset)

    # for t in (12,):  # range(0, 24, 6):
    # for t in range(0, 24, 6):
    for t in range(0, 24, 1):

        a = datetime(1979, 1, 1, t)
        b = datetime(2018, 10, 31, t)
        f.seed(rrule(DAILY, dtstart=a, until=b))


def do_params(args):
    from analogues import PARAMS
    params = list(PARAMS.keys())
    random.shuffle(params)
    for p in params:
        print(p)


ACTIONS = {
    'mars': mars_request_for_missing_fields,
    'seed': do_seed,
    'initdb': do_initdb,
    'params': do_params,
    'index': do_index,
}

if __name__ == '__main__':

    import argparse

    p = argparse.ArgumentParser()
    p.add_argument('action')

    p.add_argument('--target', type=str)
    p.add_argument('--param', type=str)
    p.add_argument('--path', type=str)
    p.add_argument('--dataset', type=str, default=DEFAULT_DATASET)
    p.add_argument('--domain', type=str, default=DEFAULT_DOMAIN)

    args = p.parse_args()

    ACTIONS[args.action](args)
