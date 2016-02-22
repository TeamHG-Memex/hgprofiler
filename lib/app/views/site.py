import json
from flask import g, jsonify, request
from flask.ext.classy import FlaskView, route
from werkzeug.exceptions import BadRequest, NotFound
from sqlalchemy.exc import IntegrityError, DBAPIError

import app.config
from app.authorization import login_required
from app.rest import (get_int_arg,
                      get_paging_arguments,
                      validate_request_json,
                      validate_json_attr)
from model import Site
import worker

# Dictionary of site attributes used for validation of json POST/PUT requests
SITE_ATTRS = {
    'name': {'type': str, 'required': True},
    'url': {'type': str, 'required': True},
    'category': {'type': str, 'required': True},
    'search_text': {'type': str, 'required': False},
    'status_code': {'type': int, 'required': False},
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
                    },
                    ...
                ],
                "total_count": 5
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

        :status 200: ok
        :status 400: invalid argument[s]
        :status 401: authentication required
        '''

        page, results_per_page = get_paging_arguments(request.args)

        query = g.db.query(Site)

        total_count = query.count()

        query = query.order_by(Site.name.asc()) \
                     .limit(results_per_page) \
                     .offset((page - 1) * results_per_page)

        sites = list()

        for site in query:
            data = site.as_dict()
            sites.append(data)

        return jsonify(
            sites=sites,
            total_count=total_count
        )

    def get(self, id_):
        '''
        '''
        pass

    def post(self):
        '''
        Create new sites to included in username searches.

        **Example Request**

        .. sourcecode:: json

            {
                "sites": [
                    {
                        "name": "",
                        "url": "",
                        "category",
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

        :status 200: created
        :status 400: invalid request body
        :status 401: authentication required
        '''
        request_json = request.get_json()
        redis = worker.get_redis()
        sites = []

        # Ensure all data is valid before db operations
        for site_json in request_json['sites']:
            validate_request_json(site_json, SITE_ATTRS)

        # Save sites
        for site_json in request_json['sites']:
            site = Site(name=site_json['name'].lower().strip(),
                        url=site_json['url'].lower().strip(),
                        category=site_json['category'].lower().strip(),
                        )

            if 'search_text' in site_json:
                site.search_text = site_json['search_text'].lower().strip()

            if 'status_code' in site_json:
                site.status_code = int(site_json['status_code'])

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
            redis.publish('site', json.dumps(site.as_dict()))

        message = '{} new sites created'.format(len(request_json['sites']))
        response = jsonify(message=message)
        response.status_code = 202

        return response

    def put(self, id_):
        '''
        Update the site identified by `id`.

            **Example Request**

            ..sourcode:: json

                {
                    {"name": "bebo"},
                    {"url": "http://bebo.com/usernames/search=%s"},
                    {"category": "social"},
                }

        **Example Response**

        ..sourcecode:: json

            {
                "id": "2",
                "name": "bebo",
                "url": "https://bebo.com/usernames/search=%s",
                "category": "social",
            }

        :<header Content-Type: application/json
        :<header X-Auth: the client's auth token
        :>json str name: the value of the name attribute

        :>header Content-Type: application/json
        :>json int id: unique identifier for label
        :>json str name: the label name
        :>json str url: URL endpoint for retriving more data about this label

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

        if 'search_text' in request_json:
            validate_json_attr('search_text', SITE_ATTRS, request_json)
            site.search_text = request_json['search_text'].lower().strip()

        if 'status_code' in request_json:
            validate_json_attr('status_code', SITE_ATTRS, request_json)
            site.status_code = int(request_json['status_code'])

        # Save the updated label
        try:
            g.db.commit()
        except DBAPIError as e:
            g.db.rollback()
            raise BadRequest('Database error: {}'.format(e))

        response = jsonify(site.as_dict())
        response.status_code = 202

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
            raise BadRequest('"{}" must be removed from all groups before deleting.'
                             .format(site.name))

        message = 'Site id "{}" deleted'.format(id_)
        response = jsonify(message=message)
        response.status_code = 200

        return response

    @route('/categories')
    def get_categories(self):
        """
        Return list of site categories.

        For now, we simply return the categories that are already set in the existing/fixture data.
        At some point, perhaps the available categories should be defined/configurable.

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
