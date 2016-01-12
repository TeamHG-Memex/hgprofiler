''' Utility functions for the REST API. '''

from datetime import datetime

from flask import url_for as flask_url_for
from sqlalchemy import case, extract, func
from werkzeug.exceptions import BadRequest


def get_int_arg(name, arg, optional=False):
    ''' Convert argument to int or return 400 BAD REQUEST. '''

    if optional and arg is None:
        return None

    try:
        arg = int(arg)
    except ValueError:
        raise BadRequest('`%s` must be an integer.' % name)

    return arg


def get_paging_arguments(args):
    ''' Get a standard pair of paging arguments from a request.args object. '''

    try:
        page = int(args.get('page', 1))
    except ValueError:
        raise BadRequest('`page` must be an integer.')

    if not page > 0:
        raise BadRequest('`page` must be greater than zero.')

    try:
        results_per_page = int(args.get('rpp', 10))
    except ValueError:
        raise BadRequest('`rpp` must be an integer.')

    if results_per_page <= 0 or results_per_page > 100:
        raise BadRequest('`rpp` must be in the range (0,100].')

    return page, results_per_page


def get_sort_arguments(args, default, allowed_fields):
    '''
    Get standard sort arguments from the URL.

    ``default`` is the default sort if none is specified in the URL.

    ``allowed_fields`` is a dictionary that maps sort key names to SQL alchemy
    columns.

    Returns a list of SQL alchemy columns suitable for passing to
    ``order_by()``.
    '''

    sort_columns = list()

    for sort in args.get('sort', default).split(','):
        if sort[0] == '-':
            descending = True
            sort = sort[1:]
        else:
            descending = False

        try:
            sort_column = allowed_fields[sort]
        except KeyError:
            raise BadRequest('Invalid sort field name')

        if descending:
            sort_column = sort_column.desc()

        sort_columns.append(sort_column.nullslast())

    return sort_columns


def isodate(datetime_):
    ''' Convert datetime to ISO-8601 without microseconds. '''
    return datetime_.replace(microsecond=0).isoformat()


def heatmap_column(column, hour, weekday):
    '''
    Return a SQL query column for counting records for a heatmap.

    The two case statements are multiplied together to form a kind of
    logical AND, which is less verbose than trying to build an elaborate,
    nested CASE statement.
    '''

    hour_case = case(
        value=extract('hour', column),
        whens={hour: 1},
        else_=0
    )

    weekday_case = case(
        value=extract('dow', column),
        whens={weekday: 1},
        else_=0
    )

    return func.sum(hour_case * weekday_case)


def url_for(*args, **kwargs):
    ''' Override Flask's url_for to make all URLS fully qualified. '''

    kwargs['_external'] = True
    return flask_url_for(*args, **kwargs)
