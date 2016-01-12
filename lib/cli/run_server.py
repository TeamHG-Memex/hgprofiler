import app
import cli


class RunServerCli(cli.BaseCli):
    """ A tool for running a development server. """

    def _get_args(self, arg_parser):
        """ Customize arguments. """

        arg_parser.add_argument(
            '--debug',
            action='store_true',
            help='Enable debug mode: errors produce stack traces and' \
                 ' the server auto reloads on source code changes.'
        )

        arg_parser.add_argument(
            '--debug-db',
            action='store_true',
            help='Print database queries.'
        )

        arg_parser.add_argument(
            '--ip',
            default='127.0.0.1',
            help='Specify an IP address to bind to. (Defaults to loopback.)'
        )

        arg_parser.add_argument(
            '--latency',
            type=float,
            metavar='L',
            help='Delay each request by <L> seconds.'
        )

    def _run(self, args, config):
        """ Main entry point. """

        flask_app = app.bootstrap(
            debug=args.debug,
            debug_db=args.debug_db,
            latency=args.latency,
            log_level=args.verbosity
        )

        # Disable secure cookies for the development server.
        flask_app.config["SESSION_COOKIE_SECURE"] = False
        flask_app.run(host=args.ip, threaded=True)
