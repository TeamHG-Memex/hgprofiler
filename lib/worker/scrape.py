import base64
import json
from datetime import datetime
import re
import sys
from urllib.parse import urljoin

import parsel
import requests

import app.database
import app.queue
import worker
from model import File, Result, Site
from model.configuration import get_config

USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) '\
             'Gecko/20100101 Firefox/40.1'


class ScrapeException(Exception):
    ''' Represents a user-facing exception. '''

    def __init__(self, message):
        self.message = message


def test_site(site_id, tracker_id, request_timeout=10):
    """
    Perform postive and negative test of site.

    Postive test: check_username() return True for existing username.
    Negative test check_username() returns False for non-existent username.

    Site is valid if:

        positive result  = 'f' (found)
        negative result = 'n' (not found)
    """
    worker.start_job()
    redis = worker.get_redis()
    db_session = worker.get_session()
    site = db_session.query(Site).get(site_id)

    # Do positive test.
    result_pos_id = check_username(username=site.test_username_pos,
                                   site_id=site_id,
                                   group_id=None,
                                   total=2,
                                   tracker_id=tracker_id + '-1',
                                   test=True)

    result_pos = db_session.query(Result).get(result_pos_id)

    # Do negative test.
    result_neg_id = check_username(username=site.test_username_neg,
                                   site_id=site_id,
                                   group_id=None,
                                   total=2,
                                   tracker_id=tracker_id + '-2',
                                   test=True)

    result_neg = db_session.query(Result).get(result_neg_id)

    # Update site with test results
    site.test_result_pos = result_pos
    site.test_result_neg = result_neg

    # Set site validity based on results
    # of both tests.
    if result_pos.status == 'f' and \
            result_neg.status == 'n':
        site.valid = True
    else:
        site.valid = False

    site.tested_at = datetime.utcnow()
    db_session.commit()

    # Send redis notification
    msg = {
        'tracker_id': tracker_id,
        'status': 'tested',
        'site': site.as_dict(),
        'resource': None,
    }
    redis.publish('site', json.dumps(msg))


def check_username(username, site_id, group_id, total,
                   tracker_id, request_timeout=10, test=False):
    """
    Check if `username` exists on the specified site.
    """

    worker.start_job()
    redis = worker.get_redis()
    db_session = worker.get_session()

    # Make a splash request.
    site = db_session.query(Site).get(site_id)
    err = None

    # Check site.
    splash_result = _splash_request(db_session, username,
                                    site, request_timeout)
    image_file = _save_image(db_session, splash_result)

    # Save result to DB.
    result = Result(
        tracker_id=tracker_id,
        site_name=splash_result['site']['name'],
        site_url=splash_result['url'],
        status=splash_result['status'],
        image_file_id=image_file.id,
        error=splash_result['error']
    )
    db_session.add(result)
    db_session.commit()

    if not test:
        # Notify clients of the result.
        current = redis.incr(tracker_id)
        result_dict = result.as_dict()
        result_dict['current'] = current
        # result_dict['image_file_url'] = image_file.url()
        # result_dict['image_name'] = image_file.name
        result_dict['total'] = total
        redis.publish('result', json.dumps(result_dict))

        # Queue archive job
        app.queue.schedule_archive(username, group_id, tracker_id)

    worker.finish_job()

    return result.id


def _check_splash_response(site, splash_response, splash_data):
    """
    Parse response and test against site criteria to determine
    whether username exists. Used with requests response object.
    """
    sel = parsel.Selector(text=splash_data['html'])
    status_ok = True
    match_ok = True

    if site.status_code is not None:
        upstream_status = splash_data['history'][0]['response']['status']
        status_ok = site.status_code == upstream_status

    if site.match_expr is not None:
        if site.match_type == 'css':
            match_ok = len(sel.css(site.match_expr)) > 0
        elif site.match_type == 'text':
            text_nodes = sel.css(':not(script):not(style)::text').extract()
            text = ''
            for text_node in text_nodes:
                stripped = text_node.strip()
                if stripped != '':
                    text += stripped + ' '
            match_ok = site.match_expr in text
        elif site.match_type == 'xpath':
            match_ok = len(sel.xpath(site.match_expr)) > 0
        else:
            raise ValueError('Unknown match_type: {}'.format(site.match_type))

    return status_ok and match_ok

def _save_image(db_session, scrape_result):
    """ Save the image returned by Splash to a local file. """
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
        # Get the generic error image.
        image_file = (
            db_session
            .query(File)
            .filter(File.name == 'hgprofiler_error.png')
            .one()
        )

    return image_file


def _splash_request(db_session, username, site, request_timeout):
    ''' Ask splash to render a page for us. '''
    target_url = site.url.replace('%s', username)
    splash_url = get_config(db_session, 'splash_url', required=True).value
    splash_headers = {
        'User-Agent': USER_AGENT,
    }
    splash_params = {
        'url': target_url,
        'html': 1,
        'jpeg': 1,
        'history': 1,
        'timeout': request_timeout,
        'resource_timeout': 5,
    }
    splash_response = requests.get(
        urljoin(splash_url, 'render.json'),
        headers=splash_headers,
        params=splash_params
    )
    result = {
        'code': splash_response.status_code,
        'error': None,
        'image': None,
        'site': site.as_dict(),
        'url': target_url,
    }

    splash_data = splash_response.json()

    try:
        splash_response.raise_for_status()

        if _check_splash_response(site, splash_response, splash_data):
            result['status'] = 'f'
        else:
            result['status'] = 'n'

        result['image'] = splash_data['jpeg']
    except Exception as e:
        result['status'] = 'e'
        result['error'] = str(e)

    return result
