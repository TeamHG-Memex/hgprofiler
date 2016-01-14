''' Message queues. '''

from rq import Queue

import app.config
import worker
import worker.scrape

_config = app.config.get_config()
_redis = app.database.get_redis(dict(_config.items('redis')))
_redis_worker = dict(_config.items('redis_worker'))
_scrape_queue = Queue('scrape', connection=_redis)


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
