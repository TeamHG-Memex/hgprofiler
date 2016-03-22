import sys
from redis import Redis
from rq import Queue, Connection, Worker

import cli
import worker


class RunWorkerCli(cli.BaseCli):
    '''
    A wrapper for RQ workers.

    Wrapping RQ is the only way to generate notifications when a job fails.
    '''

    def _get_args(self, arg_parser):
        ''' Customize arguments. '''

        arg_parser.add_argument(
            'queues',
            nargs='+',
            help='Names of queues for this worker to service.'
        )

    def _run(self, args, config):
        '''
        Main entry point.

        Adapted from http://python-rq.org/docs/workers/.
        '''

        redis_config = dict(config.items('redis'))
        port = redis_config.get('port', 6379)
        host = redis_config.get('host', 'localhost')

        with Connection(Redis(host, port)):
            queues = map(Queue, args.queues)
            w = Worker(queues, exc_handler=worker.handle_exception)
            w.work()
