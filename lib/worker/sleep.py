'''
A worker used for testing how other components handle background tasks.

This worker has 2 methods: one that sleeps but doesn't provide progress,
and another that sleeps and provides update events every 1 second.

This also serves as a good template for copy/paste when creating a new worker.
'''

import math
import time

import worker


def sleep_determinate(period):
    ''' Sleep for a specified period of time with progress updates.'''

    total_sleep = 0
    worker.start_job(total=int(math.ceil(period)))

    while total_sleep < period:
        time.sleep(1)
        total_sleep += 1
        worker.update_job(current=total_sleep)

    worker.finish_job()


def sleep_exception(period):
    ''' Sleep for a specified period then raise an exception.'''

    worker.start_job()
    time.sleep(period)
    raise ValueError('sleep_exception() is deliberately raising an exception.')


def sleep_indeterminate(period):
    ''' Sleep for a specified period of time with no progress updates.'''

    worker.start_job()
    time.sleep(period)
    worker.finish_job()
