''' Message queues. '''

from rq import Connection, Queue

import app.config
import worker
import worker.scrape
import worker.archive

_config = app.config.get_config()
_redis = app.database.get_redis(dict(_config.items('redis')))
_redis_worker = dict(_config.items('redis_worker'))
_scrape_queue = Queue('scrape', connection=_redis)
_archive_queue = Queue('archive', connection=_redis)


def dummy_job():
    '''
    This dummy job is used by init_queues().
    It must be defined at the module level so that Python RQ can import it;
    it cannot be an anonymous or nested function.
    '''
    pass


def init_queues(redis):
    '''
    Python RQ creates queues lazily, but we want them created eagerly.
    This function submits a dummy job to each queue to force Python RQ to
    create that queue.
    '''
    queues = {q for q in globals().values() if type(q) is Queue}

    with Connection(redis):
        for queue in queues:
            queue.enqueue(dummy_job)


def remove_unused_queues(redis):
    '''
    Remove queues in RQ that are not defined in this file.
    This is useful for removing queues that used to be defined but were later
    removed.
    '''
    queue_names = {q.name for q in globals().values() if type(q) is Queue}

    with Connection(redis):
        for queue in Queue.all():
            if queue.name not in queue_names:
                queue.empty()
                redis.srem('rq:queues', 'rq:queue:{}'.format(queue.name))


def schedule_username(username, group_id=None):
    ''' Queue a job to fetch results for the specified username. '''

    job = _scrape_queue.enqueue_call(
        func=worker.scrape.search_username,
        args=[username, group_id],
        timeout=_redis_worker['username_timeout']
    )

    description = 'Getting results for username "{}"'.format(username)

    worker.init_job(job=job, description=description)

    return job.id


def schedule_archive(username, job_id, results):
    ''' Queue a job to archive results for the job id. '''

    job = _archive_queue.enqueue_call(
        func=worker.archive.create_archive,
        args=[job_id, username, results],
        timeout=_redis_worker['archive_timeout']
    )

    description = 'Archiving results for username "{}"'.format(username)

    worker.init_job(job=job, description=description)
