import argparse
from datetime import datetime
import logging
import sys

import progressbar

import app.config


class CliError(Exception):
    ''' A generic error for aborting CLI scripts. '''


class BaseCli:
    ''' Base class for CLI scripts. '''

    def __init__(self):
        ''' Constructor. '''

        log_string_format = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
        log_date_format = '%Y-%m-%d %H:%M:%S'
        log_formatter = logging.Formatter(log_string_format, log_date_format)

        self._logger = logging.getLogger('cli')
        self._log_handler = logging.StreamHandler(sys.stderr)
        self._log_handler.setFormatter(log_formatter)
        self._logger.addHandler(self._log_handler)

    def get_args(self):
        ''' Parse command line arguments. '''

        arg_parser = argparse.ArgumentParser(description=self.__class__.__doc__)

        arg_parser.add_argument(
            '-v',
            dest='verbosity',
            default='info',
            choices=['debug', 'info', 'warning', 'error', 'critical'],
            help='Set logging verbosity. Defaults to "info".'
        )

        self._get_args(arg_parser)
        args = arg_parser.parse_args()
        self._logger.setLevel(getattr(logging, args.verbosity.upper()))

        return args

    def run(self):
        ''' The main entry point for all scripts. '''

        try:
            self._run(self.get_args(), app.config.get_config())
        except  CliError as e:
            self._logger.critical(str(e))
            sys.exit(1)

    def _get_args(self, arg_parser):
        '''
        Subclasses may override _get_args() to customize argument parser.
        '''

        pass

    def _progress_bar(self, name, count):
        ''' Create a progress bar with given name and total count. '''

        widgets = [
            name,
            ': ',
            progressbar.Percentage(),
            ' (',
            progressbar.SimpleProgress(),
            ')',
            ' ',
            progressbar.Bar(),
            ' ',
            progressbar.Timer(),
            ' ',
            progressbar.AdaptiveETA(),
        ]

        pbar = progressbar.ProgressBar(maxval=count, widgets=widgets)
        pbar.start()

        return pbar

    def _run(self, args, config):
        ''' Subclasses should override _run() to do their work. '''

        raise NotImplementedError()

