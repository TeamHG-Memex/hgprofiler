import json
import base64
import os
import requests
from datetime import timedelta
from tornado import httpclient, gen, ioloop, queues, escape
from urllib.parse import quote_plus

import app.database
import app.queue
from app.config import get_path
from model import Site, Result, Group
from model.configuration import get_config
import worker

USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) '\
             'Gecko/20100101 Firefox/40.1'

httpclient.AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
CONNECT_TIMEOUT = 10


class ScrapeException(Exception):
    ''' Represents a user-facing exception. '''

    def __init__(self, message):
        self.message = message


def response_contains_username(site, response):
    """
    Parse response and test against site criteria to determine whether username exists. Used with
    tornado httpclient response object.
    """
    if response.code == site.status_code:
        data = escape.json_decode(response.body)
        html = data['html'] if isinstance(data['html'], str) else data['html'].decode()
        if(site.search_text in html or
           site.search_text in response.headers):
            return True
    return False


@gen.coroutine
def save_image(image_name, bytestring):
    data_dir = get_path("data")
    screenshot_dir = os.path.join(data_dir, 'screenshot')
    image_path = os.path.join(screenshot_dir, image_name)
    with open(image_path, 'wb') as f:
        f.write(base64.decodestring(bytestring.encode('utf8')))


@gen.coroutine
def scrape_site_for_username(site, username, splash_url, request_timeout=10):
    """
    Download the page at `site.url` using Splash and parse for the username (asynchronous).
    """
    page_url = site.url.replace('%s', username)
    url = '{}/render.json?url={}&html=1&frame=1&jpeg=1'.format(splash_url, quote_plus(page_url))
    headers = {
        'User-Agent': USER_AGENT,
    }
    result = {
        'site': site,
        'found': True,
        'error': None,
        'url': page_url
    }

    try:
        response = yield httpclient.AsyncHTTPClient().fetch(url,
                                                            headers=headers,
                                                            connect_timeout=5,
                                                            validate_cert=False)

    except Exception as e:
        result['error'] = e
        result['found'] = False
        raise gen.Return(result)

    data = escape.json_decode(response.body)
    result['found'] = response_contains_username(site, response)
    result['image'] = data['jpeg']
    result['code'] = response.code

    raise gen.Return(result)


@gen.coroutine
def parse_result(scrape_result, total, job_id):
    result = Result(
        job_id=job_id,
        site_name=scrape_result['site'].name,
        site_url=scrape_result['url'],
        found=scrape_result['found'],
        total=total,
        number=1
    )
    # Save image
    if scrape_result['error'] is None:
        image_name = '{}-{}'.format(job_id, result.site_name)
        thumb_name = '{}-thumb'.format(image_name)
        image_name = '{}.jpeg'.format(image_name)
        thumb_name = '{}.jpeg'.format(thumb_name)
        try:
            save_image(image_name, scrape_result['image'])
            result.image = image_name
            result.thumb = thumb_name
        except Exception as e:
            raise ScrapeException('{}'.format(e))

    raise gen.Return(result)


@gen.coroutine
def scrape_sites(username, group_id=None):
    """
    Scrape all sites for username (asynchronous).
    """
    worker.start_job()
    job = worker.get_job()
    redis = worker.get_redis()
    db_session = worker.get_session()
    concurrency = get_config(db_session, 'scrape_concurrency', required=True).value

    try:
        concurrency = int(concurrency)
    except:
        raise ScrapeException('Value of scrape_concurrency must be an integer')

    request_timeout = get_config(db_session, 'scrape_request_timeout', required=True).value
    try:
        request_timeout = int(request_timeout)
    except:
        raise ScrapeException('Value of scrape_request_timeout must be an integer')

    splash_url = get_config(db_session, 'splash_url', required=True).value

    if group_id is not None:
        group = db_session.query(Group).get(group_id)
        sites = group.sites
    else:
        sites = db_session.query(Site).all()

    total = len(sites)
    q = queues.Queue()
    fetching, fetched = set(), set()
    results = list()

    @gen.coroutine
    def scrape_site():
        ''' Worker functions for performing scraping tasks asynchronously. '''
        current_site = yield q.get()
        try:
            if current_site in fetching:
                return

            fetching.add(current_site)
            # Scrape the page, get the result
            scrape_result = yield scrape_site_for_username(
                current_site, username, splash_url, request_timeout)
            # Parse result
            result = yield parse_result(scrape_result, total, job.id)
            db_session.add(result)
            db_session.flush()
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
    for _ in range(concurrency):
        async_worker()

    yield q.join(timeout=timedelta(seconds=300))
    assert fetching == fetched

    # Save results
    db_session.commit()


def search_username(username, group=None):
    """
    Concurrently search username across all sites using an asyncronous loop.
    """
    worker.start_job()
    io_loop = ioloop.IOLoop.current()
    io_loop.run_sync(lambda: scrape_sites(username, group))
    # Complete
    worker.finish_job()
