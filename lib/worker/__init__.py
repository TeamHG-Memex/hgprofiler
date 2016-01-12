'''
This package contains workers that handle work placed on the message queues.
'''

import json

import rq

import app.config
import app.database


_config = None
_db = None
_redis = None


def finish_job():
    ''' Mark current job as finished. '''

    job = get_job()

    if 'current' in job.meta:
        job.meta['current'] = job.meta['total']
        job.save()

    notification = json.dumps({
        'id': job.id,
        'queue': job.origin,
        'status': 'finished'
    })

    get_redis().publish('worker', notification)


def get_config():
    ''' Get application configuration. '''

    global _config

    if _config is None:
        _config = app.config.get_config()

    return _config


def get_db():
    ''' Get a database handle. '''

    global _db

    if _db is None:
        db_config = dict(get_config().items('database'))
        _db = app.database.get_engine(db_config)

    return _db


def get_job():
    ''' Return the RQ job instance. '''

    return rq.get_current_job(connection=get_redis())


def get_redis():
    ''' Get a Redis connection handle. '''

    global _redis

    if _redis is None:
        redis_config = dict(get_config().items('redis'))
        _redis = app.database.get_redis(redis_config)

    return _redis


def get_session():
    ''' Get a database session (a.k.a. transaction). '''

    return app.database.get_session(get_db())


def handle_exception(job, exc_type, exc_value, traceback):
    '''
    Handle a job exception.

    Note `return True` at the end of this function: this tells RQ to continue
    handling this exception. We only register this exception handler so that
    we can send a notification to the client.
    '''

    notification = json.dumps({
        'id': job.id,
        'status': 'failed',
        'queue': job.origin,
    })

    get_redis().publish('worker', notification)
    return True


def init_job(job, description):
    ''' Initialize job metadata. '''

    job.meta['description'] = description
    job.save()

    notification = json.dumps({
        'id': job.id,
        'status': 'queued',
        'queue': job.origin,
    })

    get_redis().publish('worker', notification)


def start_job(total=None):
    ''' Mark the current job as started. '''

    job = get_job()

    if total is not None:
        job.meta['total'] = total
        job.meta['current'] = 0
        job.save()

    notification = json.dumps({
        'id': job.id,
        'status': 'started',
        'queue': job.origin,
    })

    get_redis().publish('worker', notification)


def update_job(current):
    ''' Update the current job with new progress information. '''

    job = get_job()

    if 'total' not in job.meta:
        raise ValueError('Cannot call update_job() because job does not have '
                         'a defined total.')

    job.meta['current'] = current
    job.save()

    notification = json.dumps({
        'id': job.id,
        'status': 'progress',
        'current': current,
        'progress': current / job.meta['total'],
        'queue': job.origin,
    })

    get_redis().publish('worker', notification)
