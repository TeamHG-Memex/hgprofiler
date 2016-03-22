import redis
import sqlalchemy
from sqlalchemy import case, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import TypeDecorator, UnicodeText
from sqlalchemy.util import KeyedTuple


_engine = None
_sessionmaker = None


def get_engine(config, super_user=False):
    '''
    Get a SQLAlchemy engine from a configuration object.

    If ``super_user`` is True, then connect as super user -- typically reserved
    for issuing DDL statements.
    '''

    global _engine

    if _engine is None:
        if super_user:
            connect_string = 'postgresql+psycopg2://%(super_username)s' \
                             ':%(super_password)s@%(host)s/%(database)s?' \
                             'client_encoding=utf8'
        else:
            connect_string = 'postgresql+psycopg2://%(username)s:%(password)s' \
                             '@%(host)s/%(database)s?client_encoding=utf8'

        pool_size = config.get('pool_size', 20)
        try:
            pool_size = int(pool_size)
        except:
            raise ValueError('Configuration value pool_size must be an '
                             'integer: {}'.format(pool_size))

        _engine = sqlalchemy.create_engine(
            connect_string % config,
            pool_size=pool_size,
            pool_recycle=3600
        )

    return _engine


def get_redis(config):
    ''' Get a Redis connection handle. '''

    return redis.Redis(connection_pool=redis.ConnectionPool(**config))


def get_session(engine):
    ''' Get a SQLAlchemy session. '''

    global _sessionmaker

    if _sessionmaker is None:
        _sessionmaker = sessionmaker()

    return _sessionmaker(bind=engine)



def make_date_columns(date_column, start_date, end_date, delta, unit):
    '''
    Produce a list of query columns suitable for a time series query.

    If you want to query by a series of time spans (e.g. how many records for
    each of the last 12 months), that isn't straightforward in SQL. You can use
    COUNT(*) and group by truncated dates, but any month where the count is zero
    will be omitted from the results.

    The solution is add a column for each timespan of interest; this ensures no
    timespans are omitted, but it also makes the query quite complicated. This
    function [hopefully] simplifies the task of building that query.

    ``date_column`` is the SQL Alchemy date column to be counted.
    ``start_date`` is the date at which to start making columns. IMPORTANT: this
        date needs to be truncated to the same precision as ``unit``:
        e.g. if ``unit`` is ``month``, then ``start_date`` should have days set to 1,
        and hours, minutes, and seconds set to 0. If this date is not truncated
        correctly, you'll probably get zeroes in all of your columns!
    ``end_date`` is the date at which to stop: the last column will include
        this date.
    ``delta`` is a ``relativedelta`` object which defines the timespan covered
        by each column.
    ``unit`` is any Postgres date_trunc unit, e.g. ``week``, ``month``, ``year``, etc.
        See: http://www.postgresql.org/docs/9.1/static/functions-datetime.html#FUNCTIONS-DATETIME-TRUNC
    '''

    columns = list()
    current_date = start_date

    while current_date <= end_date:
        # This crazy thing adds one column for each month of data that we
        # want to sum up.
        columns.append(
            func.sum(case(value=func.date_trunc('month', date_column),
                          whens={current_date.isoformat(): 1},
                          else_=0)),
        )
        current_date += delta

    return columns


def query_chunks(query, id_column, chunksize=100):
    '''
    A generator that iterates over rows in a large SQL result set.

    This is more memory efficient than materializing a huge result set all
    at once, because this materializes only small chunks of the result set
    at any given time. It will issue multiple queries, if needed, to
    incrementally get the entire result set.

    It uses an `id_column` argument to efficiently page through the dataset,
    versus using an OFFSET clause, which is highly inefficient.

    *The `id_column` must be a unique, not null column, and the query must be
    sorted on this column.*
    '''

    chunk = query.limit(chunksize).all()

    while len(chunk) > 0:
        yield chunk

        # Use the ID of the last record in the previous chunk to efficiently
        # find the beginning of the next chunk.
        last_record = chunk[-1]

        if hasattr(last_record, 'id'):
            last_id = last_record.id
        elif hasattr(last_record[0], 'id'):
            last_id = last_record[0].id
        else:
            raise ValueError('No "id" field in last record.')

        chunk = query.filter(id_column > last_id) \
                     .limit(chunksize) \
                     .all()


class IntList(TypeDecorator):
    ''' Converts lists of integers to CSV string. '''

    impl = UnicodeText
    type = list

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        else:
            return ','.join(map(str,value))

    def process_result_value(self, value, dialect):
        if value is None:
            return list()
        else:
            return list(map(int, value.split(',')))
