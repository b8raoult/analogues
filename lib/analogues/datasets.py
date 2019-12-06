import sqlalchemy as db

engine = db.create_engine('sqlite:test.db', convert_unicode=True)


metadata = db.MetaData()

datasets = db.Table('datasets',
                    metadata,
                    autoload=True,
                    autoload_with=engine)
