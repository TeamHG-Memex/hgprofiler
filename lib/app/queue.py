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


def schedule_username(username, site, group_id,
                      total, tracker_id, test=False):
    '''
    Queue a job to fetch results for the specified username from the specified
    site.

    Keyword arguments:
    test -- don't archive, update site with result (default: False)
    '''

    kwargs = {
        'username': username,
        'site_id': site.id,
        'group_id': group_id,
        'total': total,
        'tracker_id': tracker_id,
        'test': test
    }

    job = _scrape_queue.enqueue_call(
        func=worker.scrape.check_username,
        kwargs=kwargs,
        timeout=_redis_worker['username_timeout']
    )

    description = 'Checking {} for user "{}"'.format(site.name, username)

    worker.init_job(job=job, description=description)

    return job.id


def schedule_archive(username, group_id, tracker_id):
    ''' Queue a job to archive results for the job id. '''

    job = _archive_queue.enqueue_call(
        func=worker.archive.create_archive,
        args=[username, group_id, tracker_id],
        timeout=_redis_worker['archive_timeout']
    )

    description = 'Archiving results for username "{}"'.format(username)

    worker.init_job(job=job, description=description)


def schedule_site_test(site, tracker_id):
    '''
    Queue a job to test a site.

    Arguments:
    site -- the site to test.
    tracker_id -- the unique tracker ID for the job.
    '''

    job = _scrape_queue.enqueue_call(
        func=worker.scrape.test_site,
        args=[site.id, tracker_id],
        timeout=30
    )

    description = 'Testing site "{}"'.format(site.name)

    worker.init_job(job=job, description=description)

    return job.id
