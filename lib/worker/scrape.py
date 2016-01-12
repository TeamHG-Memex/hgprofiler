''' Worker functions for performing scraping tasks asynchronously. '''

import json
import requests
import time
import requests.exceptions
from datetime import timedelta


import app.database
import app.queue
from model import Site, Result
import worker
from tornado import httpclient, gen, ioloop, queues

USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) '\
             'Gecko/20100101 Firefox/40.1'

httpclient.AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
CONNECT_TIMEOUT = 10
CONCURRENCY = 200


class ScrapeException(Exception):
    ''' Represents a user-facing exception. '''

    def __init__(self, message):
        self.message = message


def validate_site_response(site, response):
    """
    Parse response and test against site criteria to determine whether username exists. Used with
    python requests response object.
    """
    if response.status_code == site.status_code:
        if(site.search_text in response.text or
           site.search_text in response.headers):
            return True
    return False


def validate_response(site, response):
    """
    Parse response and test against site criteria to determine whether username exists. Used with
    tornado httpclient response object.
    """
    if response.code == site.status_code:
        html = response.body if isinstance(response.body, str) else response.body.decode()
        if(site.search_text in html or
           site.search_text in response.headers):
            return True
    return False


def scrape_site(site, username):
    """
    Download page at `site.url' and parse for username (synchronous).
    """
    url = site.url.replace('%s', username)

    headers = {
        'User-Agent': USER_AGENT
    }

    result = {
        'site': site,
        'found': True,
        'error': None,
        'url': url
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            verify=False,
            timeout=12
        )
        result['found'] = validate_site_response(site, response)
    except requests.exceptions.ConnectionError:
        result['found'] = False
        result['error'] = 'Domain does not exist'
    except requests.exceptions.Timeout:
        result['found'] = False
        result['error'] = 'Request timed out (limit 12 seconds)'
    except requests.exceptions.InvalidURL:
        result['found'] = False
        result['error'] = 'URL invalid'

    return result


def scrape_username(username):
    '''
    Scrape all sites for username (synchronous).
    '''
    worker.start_job()
    job = worker.get_job()
    redis = worker.get_redis()
    db_session = worker.get_session()
    sites = db_session.query(Site).all()
    total = len(sites)
    number = 0

    for site in sites:
        scrape_result = scrape_site(site, username)

        result = Result(
            job_id=job.id,
            site_name=scrape_result['site'].name,
            site_url=scrape_result['url'],
            found=scrape_result['found'],
            total=total,
            number=number+1
        )

        if scrape_result['error'] is not None:
            result.error = scrape_result['error']

        db_session.add(result)
        db_session.flush()
        redis.publish('result', json.dumps(result.as_dict()))
        number += 1

    # Save results
    db_session.commit()
    # Complete
    worker.finish_job()


@gen.coroutine
def scrape_site_for_username(site, username):
    """
    Download the page at `site.url` and parse for the username (asynchronous).
    """
    url = site.url.replace('%s', username)
    headers = {
        'User-Agent': USER_AGENT
    }
    result = {
        'site': site,
        'found': True,
        'error': None,
        'url': url
    }

    logging.debug('Trying {} - {}'.format(site.name, site.url))
    try:
        response = yield httpclient.AsyncHTTPClient().fetch(url,
                                                            headers=headers,
                                                            connect_timeout=CONNECT_TIMEOUT,
                                                            validate_cert=False)
        result['found'] = validate_response(site, response)

    except Exception as e:
        result['error'] = e
        result['found'] = False

    raise gen.Return(result)


@gen.coroutine
def scrape_sites(username):
    """
    Scrape all sites for username (asynchronous).
    """
    job = worker.get_job()
    redis = worker.get_redis()
    db_session = worker.get_session()
    sites = db_session.query(Site).all()
    total = len(sites)
    q = queues.Queue()
    start = time.time()
    fetching, fetched = set(), set()
    results = list()

    @gen.coroutine
    def scrape_site():
        current_site = yield q.get()
        try:
            if current_site in fetching:
                return

            fetching.add(current_site)
            scrape_result = yield scrape_site_for_username(current_site, username)
            result = Result(
                job_id=job.id,
                site_name=scrape_result['site'].name,
                site_url=scrape_result['url'],
                found=scrape_result['found'],
                total=total,
                number=1
            )
            results.append(result)
            fetched.add(current_site)
            # Notify clients of the result
            redis.publish('result', json.dumps(result.as_dict()))
        finally:
            q.task_done()

    @gen.coroutine
    def async_worker():
        while True:
            yield scrape_site()

    for site in sites:
        q.put(site)

    # Start workers, then wait for the work queue to be empty.
    for _ in range(CONCURRENCY):
        async_worker()

    yield q.join(timeout=timedelta(seconds=300))
    assert fetching == fetched

    # Save results
    db_session.add_all(results)
    db_session.commit()


def search_username(username):
    """
    Concurrently search username across all sites using an asyncronous loop.
    """
    worker.start_job()
    io_loop = ioloop.IOLoop.current()
    io_loop.run_sync(lambda: scrape_sites(username))
    # Complete
    worker.finish_job()
