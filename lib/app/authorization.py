from datetime import datetime
from functools import wraps
import urllib.parse

import dateutil.parser
from flask import g, request
from werkzeug.exceptions import BadRequest, Forbidden, Unauthorized

from model import User

def login_optional(original_function):
    '''
    A decorator that checks if a user is logged in.

    If the user is logged in, then the user object will be attached to 'g'.
    If the user is not logged in, then g.user will be None.
    '''

    @wraps(original_function)
    def wrapper(*args, **kwargs):
        g.user = _get_user_from_request(required=False)
        return original_function(*args, **kwargs)

    return wrapper

def login_required(original_function):
    '''
    A decorator that requires a user to be logged in.

    A user is logged in if the user has a valid auth header that
    refers to a valid user object. If the user is logged in, then
    the user object will be attached to 'g'.
    '''

    @wraps(original_function)
    def wrapper(*args, **kwargs):
        g.user = _get_user_from_request(required=True)
        return original_function(*args, **kwargs)

    return wrapper

def admin_required(original_function):
    '''
    A decorator that requires a logged in user to be an admin.

    If the user is an admin, then the user object will be attached to 'g'.

    Raises 401 HTTP exception if user is not logged or 403 HTTP exception if
    the user is logged in but is not an admin.
    '''

    @wraps(original_function)
    def wrapper(*args, **kwargs):
        user = _get_user_from_request(required=True)

        if not user.is_admin:
            raise Forbidden("This request requires administrator privileges.")

        g.user = user

        return original_function(*args, **kwargs)

    return wrapper

def _get_user_from_request(required=True):
    '''
    Verify auth token is valid (not tampered with) and matches real user.

    Returns the current user object if auth token is valid and matches a real
    user.

    Note that the authentication token can be passed as a header (preferred) or
    in the query string. Passing in the query string is only recommended for
    situations where headers cannot be controlled, such as `<img src='...'>`
    or EventSource('...').

    If token is invalid or is valid but no user matches, then:
    1. If `required` is True, raise 401 HTTP exception.
    2. If `required` is False, return None.
    '''

    if 'X-Auth' in request.headers:
        xauth = request.headers['X-Auth']
    elif 'xauth' in request.args:
        xauth = request.args['xauth']
    else:
        xauth = None

    try:
        token = g.unsign(xauth).decode('ascii').split('|')
        user_id = int(token[0])
        expires = dateutil.parser.parse(token[1])

        if expires < datetime.now():
            raise ValueError()

        user = g.db.query(User).filter(User.id==user_id).one()

    except:
        if required:
            raise Unauthorized("Invalid auth token.")
        else:
            user = None

    return user
