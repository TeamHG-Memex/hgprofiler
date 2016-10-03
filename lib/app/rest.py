''' Utility functions for the REST API. '''
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


def validate_json_attr(attr_name, attrs, request_json):
    '''
    Validate request_json to ensure that the the attribute `attr_name` conforms
    to the criteria specified by the `attrs` dictionary.

    Raise BadRequest on failure.

    Requires that strings are not empty.

    **Example**

        attrs = {
            'name': {'type': str, 'required': True},
            'url': {'type': str, 'required': True},
            'category': {'type': str, 'required': True},
            'search_text': {'type': str, 'required': False},
            'status_code': {'type': int,
                            'required': False,
                            'allow_null': True},
        }

        request_json = request.get_json() # Flask request object
        validate_json_attr('name', attrs, request_json)
        validate_json_attr('url', attrs, request_json)
        ...
    '''
    # Confirm attribute exists in attrs.
    try:
        attr_type = attrs[attr_name]['type']
    except KeyError:
        raise BadRequest('Attribute "{}" does not exist.'.format(attr_name))

    # Confirm attribute exists in request_json.
    try:
        val = request_json[attr_name]
    except KeyError:
        raise BadRequest('{} is required.'.format(attr_name))

    # Confirm that the attribute is not None
    try:
        allow_null = attrs[attr_name]['allow_null']
    except KeyError:
        allow_null = False

    if not allow_null and val is None:
        raise BadRequest('{} cannot be null.'.format(attr_name))

    # Confirm attribute is of correct type.
    if val is not None:
        try:
            attr_type(val)
        except ValueError:
            msg = '{} must be {}.'
            raise BadRequest(msg.format(attr_name, attr_type.__name__))

    # If attr_name is a string, confirm that it is not empty.
    if attr_type == str and val is not None and val.strip() == '':
        raise BadRequest('{} cannot be empty.'.format(attr_name))


def validate_request_json(request_json, attrs):
    '''
    Validate `request_json` for all attributes in `attrs`.
    Calls validate_json_attr() on each attribute.

    **Example**
        attrs = {
            'name': {'type': str, 'required': True},
            'url': {'type': str, 'required': True},
            'category': {'type': str, 'required': True},
            'search_text': {'type': str, 'required': False},
            'status_code': {'type': int, 'required': False},
        }

        request_json = request.get_json() # Flask request object
        validate_request_json(request_json, attrs)
    '''
    for attr_name, attr_meta in attrs.items():
        if attr_meta['required']:
            validate_json_attr(attr_name, attrs, request_json)
        else:
            if attr_name in request_json:
                validate_json_attr(attr_name, attrs, request_json)
