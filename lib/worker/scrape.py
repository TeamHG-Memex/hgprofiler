import json
import base64
from datetime import timedelta
from tornado import httpclient, gen, ioloop, queues, escape
from urllib.parse import quote_plus

import app.database
import app.queue
from model import Site
from model import Result
from model import Group
from model import File
from model.configuration import get_config
import worker

USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) '\
             'Gecko/20100101 Firefox/40.1'

httpclient.AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")


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
        if(site.search_text in html.lower() or
           site.search_text in response.headers):
            return True
    return False


@gen.coroutine
def scrape_site_for_username(site, username, splash_url, request_timeout=10):
    """
    Download the page at `site.url` using Splash and parse for the username (asynchronous).
    """
    page_url = site.url.replace('%s', username)
    url = '{}/render.json?url={}&html=1&frame=1&jpeg=1&timeout={}&resource_timeout=5'.format(
        splash_url, quote_plus(page_url), request_timeout)
    headers = {
        'User-Agent': USER_AGENT,
    }
    result = {
        'site': site.as_dict(),
        'error': None,
        'url': page_url,
        'image': None
    }
    async_http = httpclient.AsyncHTTPClient()
    try:
        response = yield async_http.fetch(url,
			                  headers=headers,
					  connect_timeout=5,
					  request_timeout=request_timeout+3,
					  validate_cert=False)
    except httpclient.HTTPError as e:
        error = '{}'.format(e)
        # Catch Splash timeout
        if '599' in error:
            error = 'Splash connection failed'
        else:
            # Errors returned by Splash
            try:
                data = escape.json_decode(e.response.body)
                if 'error' in data:
                    if data['error'] == 504:
                        error = 'Timeout'
                    else:
                        error = data['description']
                else:
                    error = 'Splash failed to retrieve page'
            except:
                pass
        result['error'] = error
        result['status'] = 'e'

        raise gen.Return(result)

    data = escape.json_decode(response.body)

    if response_contains_username(site, response):
        result['status'] = 'f'
    else:
        result['status'] = 'n'

    result['image'] = data['jpeg']
    result['code'] = response.code

    raise gen.Return(result)


@gen.coroutine
def save_image(scrape_result):
    db_session = worker.get_session()

    # Save image
    if scrape_result['error'] is None:
        image_name = '{}.jpg'.format(scrape_result['site']['name'])
        content = base64.decodestring(scrape_result['image'].encode('utf8'))
        image_file = File(name=image_name,
                          mime='image/jpeg',
                          content=content)
        db_session.add(image_file)

        try:
            db_session.commit()
        except:
            db_session.rollback()
            raise ScrapeException('Could not save image')

    else:
        image_file = db_session.query(File).filter(File.name == 'hgprofiler_error.png').one()

    raise gen.Return(image_file)

def parse_result(scrape_result, image_file, total, job_id):
    ''' 
    Map variables to a Result model.
    '''
    result = Result(
        job_id=job_id,
        site_name=scrape_result['site']['name'],
        site_url=scrape_result['url'],
        status=scrape_result['status'],
        image_file_id=image_file.id,
        total=total,
        number=1
    )
    return result




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
            image_file = yield save_image(scrape_result)
            result = parse_result(scrape_result, image_file, total, job.id)
            db_session.add(result)
            db_session.flush()
            fetched.add(current_site)
            
            # Add image data for redis
            result_dict = result.as_dict()
            result_dict['image_file_url'] = image_file.url()
            result_dict['image_name'] = image_file.name
            # Notify clients of the result
            redis.publish('result', json.dumps(result_dict))
            # Add image file path for archive creation  - don't want to publish on Redis.
            result_dict['image_file_path'] = result.image_file.relpath()
            results.append(result_dict)
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

    # Save results to db
    db_session.commit()
    # Queue worker to create archive db record and zip file.
    app.queue.schedule_archive(username, group_id, job.id, results)


def search_username(username, group=None):
    """
    Concurrently search username across all sites using an asyncronous loop.
    """
    worker.start_job()
    io_loop = ioloop.IOLoop.current()
    io_loop.run_sync(lambda: scrape_sites(username, group))
    # Complete
    worker.finish_job()
