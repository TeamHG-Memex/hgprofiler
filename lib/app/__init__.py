""" The main application package. """

import logging
import sys
import time

from flask import Flask, g, jsonify, make_response, request
from flask.ext.assets import Environment, Bundle
from flask_failsafe import failsafe
from itsdangerous import Signer
from werkzeug.exceptions import HTTPException

import app.config
import app.database
from app.queue import init_queues, remove_unused_queues


flask_app = None


class MyFlask(Flask):
    """
    Customized Flask subclass.

    Features:
     * Changes jinja2 delimiters from {{foo}} to [[foo]].
    """

    jinja_options = Flask.jinja_options.copy()
    jinja_options.update({
        "block_start_string": "[%",
        "block_end_string":   "%]",
        "variable_start_string": "[[",
        "variable_end_string":   "]]",
        "comment_start_string": "[#",
        "comment_end_string":   "#]",
    })

    __atexit = list()

    @classmethod
    def atexit(cls, function):
        ''' Register a function to run before Flask shuts down. '''
        cls.__atexit.append(function)

    def run(self, *args, **kwargs):
        ''' Override run() so we can run callbacks during SystemExit. '''

        try:
            super().run(*args, **kwargs)
        except SystemExit:
            for function in self.__class__.__atexit:
                function()
            raise


@failsafe
def bootstrap(debug=False, debug_db=False, latency=None, log_level=None):
    """ Bootstrap the Flask application and return a reference to it. """

    global flask_app

    if flask_app is not None:
        raise RuntimeError("The application should not be"
                           " bootstrapped more than once.")

    # Initialize Flask.
    flask_app = MyFlask(
        __name__,
        static_folder=app.config.get_path("static"),
        template_folder=app.config.get_path("lib/app/templates")
    )

    flask_app.debug = debug
    flask_app.debug_db = debug_db
    flask_app.latency = latency

    config = app.config.get_config()

    if log_level is not None:
        config.set('logging', 'log_level', log_level)

    # Run the bootstrap.
    init_logging(flask_app, config)
    init_flask(flask_app, config)
    init_errors(flask_app, config)
    init_webassets(flask_app, config)
    init_views(flask_app, config)

    return flask_app


def init_errors(flask_app, config):
    ''' Initialize error handlers. '''

    def http_error_handler(error):
        '''
        An error handler that will convert errors to JSON format if necessary.
        '''

        if not isinstance(error, HTTPException):
            raise error

        # TODO Should use a real mime parser here…
        mimetype = request.headers.get('accept', '').strip()

        if hasattr(error, 'description'):
            description = error.description
        else:
            description = str(error)

        if mimetype.startswith('application/json'):
            response = jsonify(message=description)
        else:
            response = make_response(description + '\n\n')
            response.headers['Content-type'] = 'text/plain'

        response.status_code = error.code

        return response

    http_status_codes = list(range(400, 418)) + list(range(500, 506))

    for http_status_code in http_status_codes:
        flask_app.errorhandler(http_status_code)(http_error_handler)


def init_flask(flask_app, config):
    """ Initialize Flask configuration and hooks. """

    config_dict = dict(config.items('flask'))

    # Try to convert numeric arguments to integers.
    for k, v in config_dict.items():
        try:
            config_dict[k] = int(v)
        except:
            pass

    flask_app.config.update(**config_dict)

    # Disable caching for static assets in debug mode, otherwise
    # many Angular templates will be stale when refreshing pages.
    if flask_app.debug:
        flask_app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

    db_engine = app.database.get_engine(dict(config.items('database')))
    redis = app.database.get_redis(dict(config.items('redis')))
    remove_unused_queues(redis)
    init_queues(redis)

    signer = Signer(config.get('flask', 'SECRET_KEY'))
    sign_fn = lambda s: signer.sign(str(s).encode('utf8')).decode('utf-8')
    unsign_fn = signer.unsign

    @flask_app.after_request
    def after_request(response):
        ''' Clean up request context. '''

        g.db.close()

        return response

    if flask_app.latency is not None:
        @flask_app.before_request
        def api_latency():
            if request.path[:5] == '/api/':
                time.sleep(flask_app.latency)

    @flask_app.before_request
    def before_request():
        ''' Initialize request context. '''

        g.config = config
        g.debug = flask_app.debug
        g.db = app.database.get_session(db_engine)
        g.redis = redis
        g.sign = sign_fn
        g.unsign = unsign_fn

    @flask_app.url_defaults
    def static_asset_cache_busting(endpoint, values):
        if endpoint == 'static' and 'filename' in values:
            filename = values['filename']
            if filename.startswith('img') or \
               filename.startswith('fonts'):

                values['version'] = flask_app.config['VERSION']

    if flask_app.debug:
        flask_app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0


def init_logging(flask_app, config):
    """
    Set up logging.

    Flask automatically writes to stderr in debug mode, so we only configure
    the Flask log in production mode.
    """

    log_string_format = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
    log_date_format = '%Y-%m-%d %H:%M:%S'
    log_formatter = logging.Formatter(log_string_format, log_date_format)

    try:
        log_level = getattr(logging, config.get('logging', 'log_level').upper())
    except AttributeError:
        raise ValueError("Invalid log level: %s" % log_level)

    if not flask_app.debug:
        log_file = config.get('logging', 'log_file')
        log_handler = logging.FileHandler(log_file)
        log_handler.setLevel(log_level)
        log_handler.setFormatter(log_formatter)

        flask_app.logger.addHandler(log_handler)

    if flask_app.debug_db:
        # SQL Alchemy logging is very verbose and is only turned on when
        # explicitly asked for.
        db_log_handler = logging.StreamHandler(sys.stderr)
        db_log_handler.setFormatter(log_formatter)

        db_logger = logging.getLogger('sqlalchemy.engine')
        db_logger.setLevel(logging.INFO)
        db_logger.addHandler(db_log_handler)


def init_views(flask_app, config):
    """ Initialize views. """

    from app.views.api_index import ApiIndexView
    ApiIndexView.register(flask_app, route_base='/api/')

    from app.views.authenticate import AuthenticationView
    AuthenticationView.register(flask_app, route_base='/api/authentication/')

    from app.views.configuration import ConfigurationView
    ConfigurationView.register(flask_app, route_base='/api/configuration/')

    from app.views.file import FileView
    FileView.register(flask_app, route_base='/api/file/')

    from app.views.notification import NotificationView
    NotificationView.register(flask_app, route_base='/api/notification/')
    flask_app.atexit(NotificationView.quit_notifications)

    from app.views.site import SiteView
    SiteView.register(flask_app, route_base='/api/site/')

    from app.views.tasks import TasksView
    TasksView.register(flask_app, route_base='/api/tasks/')

    from app.views.user import UserView
    UserView.register(flask_app, route_base='/api/user/')

    from app.views.username import UsernameView
    UsernameView.register(flask_app, route_base='/api/username/')

    from app.views.group import GroupView
    GroupView.register(flask_app, route_base='/api/group/')

    # Make sure to import the Angular view last so that it will match
    # all remaining routes.
    import app.views.angular


def init_webassets(flask_app, config):
    """ Initialize Flask-Assets extension. """

    assets = Environment(flask_app)
    assets.debug = flask_app.debug

    dart_root = 'dart/web' if flask_app.debug else 'dart/build/web'

    assets.register("less",  Bundle(
        "less/bootstrap/bootstrap.less",
        "less/font-awesome/font-awesome.less",
        filters="less",
        output="combined/bootstrap.css",
        depends="less/*.less"
    ))

    assets.register('dart', Bundle(
        dart_root + '/main.dart'
    ))

    assets.register("javascript", Bundle(
        'js/d3.js',
        'js/markdown.js',
        dart_root + '/packages/web_components/dart_support.js',
        dart_root + '/packages/browser/dart.js',
        output='combined/combined.js'
    ))
