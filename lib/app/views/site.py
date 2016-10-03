from flask import g, jsonify, request
from flask.ext.classy import FlaskView, route
from werkzeug.exceptions import BadRequest, NotFound
from sqlalchemy.exc import IntegrityError, DBAPIError

import app.queue
from app.authorization import login_required
from app.notify import notify_mask_client
from app.rest import (get_int_arg,
                      get_paging_arguments,
                      validate_request_json,
                      validate_json_attr)
from helper.functions import random_string
from model import Site

# Dictionary of site attributes used for validation of json POST/PUT requests
SITE_ATTRS = {
    'name': {'type': str, 'required': True},
    'url': {'type': str, 'required': True},
    'category': {'type': str, 'required': True},
    'match_expr': {'type': str, 'required': False, 'allow_null': True},
    'match_type': {'type': str, 'required': False, 'allow_null': True},
    'status_code': {'type': int, 'required': False, 'allow_null': True},
    'test_username_pos': {'type': str, 'required': True},
    'test_username_neg': {'type': str, 'required': False},
}


class SiteView(FlaskView):
    '''
    Data about profiler sites.
    '''

    decorators = [login_required]

    def index(self):
        '''
        Return an array of data about sites.

        **Example Response**

        .. sourcecode:: json

            {
                "sites": [
                    {
                        "category": "social",
                        "id": 1,
                        "name": "Blinklist",
                        "search_text": "BlinkList Page.</title>",
                        "status_code": 200,
                        "url": "https://app.blinklist.com/users/%s",
                        "test_username_pos": "john",
                        "test_username_neg": "dPGMFrf72SaS",
                        "test_status": "f",
                        "tested_at": "2016-01-01T00:00:00.000000+00:00",
                    },
                    ...
                ],
                "total_count": 5,
                "total_valid_count": 5,
                "total_invalid_count": 0,
                "total_tested_count": 5
            }

        :<header Content-Type: application/json
        :<header X-Auth: the client's auth token
        :query page: the page number to display (default: 1)
        :query rpp: the number of results per page (default: 10)

        :>header Content-Type: application/json
        :>json list sites: a list of site objects
        :>json str sites[n].category: the category of this site
        :>json int sites[n].id: the unique id of this site
        :>json str sites[n].name: the name of this site
        :>json str sites[n].search_text: the text pattern should that should
            exist in the body or headers of a successful search result page
        :>json str sites[n].status_code: the server response code that should
            be returned with a successful search result
        :>json str sites[n].url: the url of this site where username search can
            be performed
        :>json str sites[n].test_status: results of username test
        :>json str sites[n]tested_at: timestamp of last test
        :>json str sites[n].test_username_pos: the username that exists
            on the site (used for testing)
        :>json str sites[n].test_username_neg: the username that
            does not exist on the site (used for testing)

        :status 200: ok
        :status 400: invalid argument[s]
        :status 401: authentication required
        '''

        page, results_per_page = get_paging_arguments(request.args)

        query = g.db.query(Site)

        total_count = query.count()
        total_valid_count = query.filter(Site.valid == True).count() # noqa
        total_invalid_count = query.filter(Site.valid == False).count() # noqa
        total_tested_count = query.filter(Site.tested_at != None).count() # noqa

        query = query.order_by(Site.name.asc()) \
                     .limit(results_per_page) \
                     .offset((page - 1) * results_per_page)

        sites = list()

        for site in query:
            data = site.as_dict()
            sites.append(data)

        return jsonify(
            sites=sites,
            total_count=total_count,
            total_valid_count=total_valid_count,
            total_invalid_count=total_invalid_count,
            total_tested_count=total_tested_count,
        )

    def get(self, id_):
        raise BadRequest('End point not configured')

    def post(self):
        '''
        Create new sites to included in username searches.

        **Example Request**

        .. sourcecode:: json

            {
                "sites": [
                    {
                        "name": "about.me",
                        "url": "http://about.me/%s",
                        "category": "social",
                        "status_code": 200,
                        "match_type": "text",
                        "match_expr": "Foo Bar Baz",
                        "test_username_pos": "john",
                        "test_username_neg": "dPGMFrf72SaS"
                    },
                    ...
                ]
            }

        **Example Response**

        .. sourcecode:: json

            {
                "message": "1 site created."
            }

        :<header Content-Type: application/json
        :<header X-Auth: the client's auth token
        :>json list sites: a list of sites to create
        :>json string sites[n].name: name of site
        :>json string sites[n].url: username search url for the site
        :>json string sites[n].category: category of the site
        :>json int sites[n].status_code: the status code to check for
            determining a match (nullable)
        :>json string sites[n].match_type: type of match (see get_match_types()
            for valid match types) (nullable)
        :>json string sites[n].match_expr: expression to use for determining
            a page match (nullable)
        :>json string sites[n].test_username_pos: username that exists on site
            (used for testing)
        :>json string sites[n].test_username_neg: username that does not exist
            on site (used for testing)

        :status 200: created
        :status 400: invalid request body
        :status 401: authentication required
        '''
        request_json = request.get_json()
        sites = []

        # Ensure all data is valid before db operations
        for site_json in request_json['sites']:
            validate_request_json(site_json, SITE_ATTRS)

            if (site_json['match_type'] is None or \
                site_json['match_expr'] is None) and \
                site_json['status_code'] is None:
                raise BadRequest('At least one of the following is required: '
                    'status code or page match.')

        # Save sites
        for site_json in request_json['sites']:
            test_username_pos = site_json['test_username_pos'].lower().strip()
            site = Site(name=site_json['name'].lower().strip(),
                        url=site_json['url'].lower().strip(),
                        category=site_json['category'].lower().strip(),
                        test_username_pos=test_username_pos)

            site.status_code = site_json['status_code']
            site.match_expr = site_json['match_expr']
            site.match_type = site_json['match_type']

            if 'test_username_neg' in site_json:
                site.test_username_neg = site_json['test_username_neg'] \
                    .lower().strip(),

            g.db.add(site)

            try:
                g.db.flush()
                sites.append(site)
            except IntegrityError:
                g.db.rollback()
                raise BadRequest(
                    'Site URL {} already exists.'.format(site.url)
                )

        g.db.commit()

        # Send redis notifications
        for site in sites:
            notify_mask_client(
                channel='site',
                message={
                    'id': site.id,
                    'name': site.name,
                    'status': 'created',
                    'resource': None
                }
            )

        message = '{} new sites created'.format(len(request_json['sites']))
        response = jsonify(message=message)
        response.status_code = 202

        return response

    def put(self, id_):
        '''
        Update the site identified by `id`.

        **Example Request**

        ..sourcecode:: json

            {
                {
                    "name": "bebo",
                    "url": "http://bebo.com/usernames/search=%s",
                    "category": "social",
                    "status_code": 200,
                    "match_type": "text",
                    "match_expr": "Foo Bar Baz",
                    "test_username_pos": "bob",
                    "test_username_ne": "adfjf393rfjffkjd",
                }
            }

        **Example Response**

        ..sourcecode:: json

            {
                "category": "social",
                "id": 2,
                "name": "bebo",
                "search_text": "Bebo User Page.</title>",
                "status_code": 200,
                "match_type": "text",
                "match_expr": "Foo Bar Baz",
                "url": "https://bebo.com/usernames/search=%s",
                "test_username_pos": "bob",
                "test_username_neg": "adfjf393rfjffkjd",
                "test_status": "f",
                "tested_at": "2016-01-01T00:00:00.000000+00:00",
            },

        :<header Content-Type: application/json
        :<header X-Auth: the client's auth token
        :>json string name: name of site
        :>json string url: username search url for the site
        :>json string category: category of the site
        :>json string test_username_pos: username that exists on site
            (used for testing)
        :>json string test_username_neg: username that does not
            exist on site (used for testing)

        :>header Content-Type: application/json
        :>json int id: unique identifier for site
        :>json str name: name of site
        :>json str url: username search url for the site
        :>json str category: category of the site
        :>json int status_code: the status code to check for
            determining a match (nullable)
        :>json string match_type: type of match (see get_match_types()
            for valid match types) (nullable)
        :>json string match_expr: expression to use for determining
            a page match (nullable)
        :>json str test_status: results of username test
        :>json str tested_at: timestamp of last test
        :>json str test_username_pos: username that exists on site
            (used for testing)
        :>json str test_username_neg: username that does not
            exist on site (used for testing)

        :status 202: updated
        :status 400: invalid request body
        :status 401: authentication required
        :status 404: site does not exist
        '''

        # Get site.
        id_ = get_int_arg('id_', id_)
        site = g.db.query(Site).filter(Site.id == id_).first()

        if site is None:
            raise NotFound("Site '%s' does not exist." % id_)

        request_json = request.get_json()

        # Validate data and set attributes
        if 'name' in request_json:
            validate_json_attr('name', SITE_ATTRS, request_json)
            site.name = request_json['name'].lower().strip()

        if 'url' in request_json:
            validate_json_attr('url', SITE_ATTRS, request_json)
            site.url = request_json['url'].lower().strip()

        if 'category' in request_json:
            validate_json_attr('category', SITE_ATTRS, request_json)
            site.category = request_json['category'].lower().strip()

        if 'match_expr' in request_json:
            validate_json_attr('match_expr', SITE_ATTRS, request_json)
            site.match_expr = request_json['match_expr']

        if 'match_type' in request_json:
            validate_json_attr('match_type', SITE_ATTRS, request_json)
            site.match_type = request_json['match_type'].strip()

        if 'status_code' in request_json:
            validate_json_attr('status_code', SITE_ATTRS, request_json)
            status = request_json['status_code']
            site.status_code = None if status is None else int(status)

        if (request_json['match_type'] is None or \
            request_json['match_expr'] is None) and \
            request_json['status_code'] is None:
            raise BadRequest('At least one of the following is required: '
                'status code or page match.')

        if 'test_username_pos' in request_json:
            validate_json_attr('test_username_pos', SITE_ATTRS, request_json)
            site.test_username_pos = (request_json['test_username_pos']
                                      .lower()
                                      .strip())

        if 'test_username_neg' in request_json:
            validate_json_attr('test_username_neg', SITE_ATTRS, request_json)
            site.test_username_neg = (request_json['test_username_neg']
                                      .lower()
                                      .strip())

        # Save the updated site
        try:
            g.db.commit()
        except DBAPIError as e:
            g.db.rollback()
            raise BadRequest('Database error: {}'.format(e))

        # Send redis notifications
        notify_mask_client(
            channel='site',
            message={
                'site': site.as_dict(),
                'status': 'updated',
                'resource': None
            }
        )

        response = jsonify(site.as_dict())
        response.status_code = 200

        # Send response.
        return response

    def delete(self, id_):
        '''
        Delete site identified by `id_`.
        '''
        # Get site.
        id_ = get_int_arg('id_', id_)
        site = g.db.query(Site).filter(Site.id == id_).first()

        if site is None:
            raise NotFound("Site '%s' does not exist." % id_)

        # Delete site
        try:
            g.db.delete(site)
            g.db.commit()
        except IntegrityError:
            g.db.rollback()
            raise BadRequest('"{}" must be removed from all groups '
                             'before deleting.'
                             .format(site.name))

        # Send redis notifications
        notify_mask_client(
            channel='site',
            message={
                'id': site.id,
                'name': site.name,
                'status': 'deleted',
                'resource': None
            }
        )

        message = 'Site id "{}" deleted'.format(id_)
        response = jsonify(message=message)
        response.status_code = 200

        return response

    @route('/job/', methods=['POST'])
    def post_jobs_for_sites(self):
        """
        Request background jobs for all sites.

        **Example Request**

        ..sourcode:: json

            {
                "jobs": [
                    {
                        "name": "test",
                    },
                    ...
                ]
            }

        **Example Response**

        .. sourcecode:: json

            {
                "tracker_ids": {
                        "1": "tracker.12344565",
                }

            }

        :<header Content-Type: application/json
        :<header X-Auth: the client's auth token
        :>json list jobs: a list of jobs to schedule
        :>json string jobs[n].name: name of job

        :>header Content-Type: application/json
        :>json array tracker_ids: array of worker tracking ids

        :status 202: scheduled
        :status 400: invalid request body
        :status 401: authentication required
        """
        request_attrs = {
            'jobs': {'type': list, 'required': True},
        }
        job_attrs = {
            'name': {'type': str, 'required': True},
        }
        available_jobs = ['test']
        tracker_ids = dict()

        request_json = request.get_json()
        validate_request_json(request_json, request_attrs)

        for job in request_json['jobs']:
            validate_json_attr('name', job_attrs, job)

            if job['name'] not in available_jobs:
                raise BadRequest(
                    '`{}` does not exist in available'
                    ' jobs: {}'
                    .format(job['name'],
                            ','.join(available_jobs)))

        # Get sites.
        sites = g.db.query(Site).all()

        # Schedule jobs
        for job in request_json['jobs']:
            for site in sites:
                tracker_id = 'tracker.{}'.format(random_string(10))
                tracker_ids[site.id] = tracker_id

                if job['name'] == 'test':
                    app.queue.schedule_site_test(
                        site=site,
                        tracker_id=tracker_id,
                    )

        response = jsonify(tracker_ids=tracker_ids)
        response.status_code = 202

        return response

    @route('/<int:site_id>/job', methods=['POST'])
    def post_jobs_for_site(self, site_id):
        """
        Request background jobs for site identified by `id`.

        **Example Request**

        ..sourcode:: json

            {
                "jobs": [
                    {
                        "name": "test",
                    },
                    ...
                ]
            }

        **Example Response**

        .. sourcecode:: json

            {
                "tracker_ids": {
                        "1": "tracker.12344565",
                }
            }

        :<header Content-Type: application/json
        :<header X-Auth: the client's auth token
        :>json list jobs: a list of jobs to schedule
        :>json string jobs[n].name: name of job

        :>header Content-Type: application/json
        :>json array tracker_ids: array of worker tracking ids
            {site ID: tracker ID}

        :status 202: scheduled
        :status 400: invalid request body
        :status 401: authentication required
        """
        request_attrs = {
            'jobs': {'type': list, 'required': True},
        }
        job_attrs = {
            'name': {'type': str, 'required': True},
        }
        available_jobs = ['test']
        tracker_ids = dict()

        # Get site.
        site_id = get_int_arg('site_id', site_id)
        site = g.db.query(Site).filter(Site.id == site_id).first()

        # Validate
        if site is None:
            raise NotFound("Site '%s' does not exist." % site_id)

        request_json = request.get_json()
        validate_request_json(request_json, request_attrs)

        for job in request_json['jobs']:
            validate_json_attr('name', job_attrs, job)

            if job['name'] not in available_jobs:
                raise BadRequest(
                    '`{}` does not exist in available'
                    ' jobs: {}'
                    .format(job['name'],
                            ','.join(available_jobs)))

        # Schedule jobs
        for job in request_json['jobs']:
            tracker_id = 'tracker.{}'.format(random_string(10))
            tracker_ids[site.id] = tracker_id

            if job['name'] == 'test':
                app.queue.schedule_site_test(
                    site=site,
                    tracker_id=tracker_id,
                )

        response = jsonify(tracker_ids=tracker_ids)
        response.status_code = 202

        return response

    @route('/categories')
    def get_categories(self):
        """
        Return list of site categories.

        For now, we simply return the categories that are already
        set in the existing/fixture data.

        At some point, perhaps the available categories should
        be defined/configurable.

        **Example Response**

        ..sourcecode:: json

            {
                "categories": [
                    "books",
                    "images",
                    "pressies",
                ]
            }

        :<header Content-Type: application/json
        :<header X-Auth: the client's auth token

        :>header Content-Type: application/json
        :>json list categories: list of site categories
        :>json str url: URL endpoint for retriving more data about this label

        :status 200: ok
        :status 400: invalid request body
        :status 401: authentication required
        """
        categories = g.db.query(Site.category).distinct()
        categories = [c[0] for c in categories]
        categories.sort()

        response = jsonify(categories=categories)
        response.status_code = 200

        return response

    @route('/match-types')
    def get_match_types(self):
        '''
        Return a dict that maps match types to their human-readable
        descriptions.

        **Example Response**

        .. sourcecode:: json

            {
                "match_types": {
                    'css': 'CSS Selector',
                    'text': 'Text On Page',
                    'xpath': 'XPath Query',
                }
            }

        :<header Content-Type: application/json
        :<header X-Auth: the client's auth token

        :>header Content-Type: application/json
        :>json dict match_types: a dict of match types

        :status 200: ok
        :status 401: authentication required
        '''

        return jsonify(match_types=Site.MATCH_TYPES)
