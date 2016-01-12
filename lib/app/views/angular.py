""" Views for the index. """

from flask import render_template, request
from werkzeug.exceptions import NotFound

from app import flask_app

@flask_app.route('/', defaults={'path': None})
@flask_app.route('/<path:path>')
def angular(path):
    """
    Serves the main Angular template.

    This matches _all_ routes so that we can use HTML5 push state for
    client side routing while still allowing deep links. Therefore, this
    route should be added after all other routes.
    """

    if path is not None and path.startswith('api/'):
        raise NotFound('There is no API endpoint matching "%s".' % path)

    return render_template("root.html")
