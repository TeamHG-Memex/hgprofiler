import json
from flask import g, jsonify, request
from flask.ext.classy import FlaskView
from sqlalchemy.exc import IntegrityError, DBAPIError
from werkzeug.exceptions import BadRequest, NotFound

import worker
import app.config
import app.queue
from app.authorization import login_required
from app.rest import (get_int_arg,
                      url_for,
                      get_paging_arguments,
                      validate_request_json,
                      validate_json_attr)
from model.group import Group
from model.site import Site

# Dictionary of group attributes used for validation of json POST/PUT requests
GROUP_ATTRS = {
    'name': {'type': str, 'required': True},
    'sites': {'type': list, 'required': True},
}

class GroupView(FlaskView):
    '''
    Create, edit and retrieve sites groups used for username search.
    '''

    decorators = [login_required]

    def get(self, id_):
        '''
        Get the group identified by `id`.

        **Example Response**

        .. sourcecode: json

            {
                "id": 1,
                "name": "gender",
                "sites": [
                    {
                        "id": 2,
                        "name": "",
                        "url": "".
                        "status_code": "",
                        "search_pattern": "",
                        "category": ""
                    },
                    ...
                ]
            }

        :<header Content-Type: application/json
        :<header X-Auth: the client's auth token

        :>header Content-Type: application/json
        :>json int id: unique identifier for group
        :>json str name: the group name
        :>json str url: URL url-for for retriving more data about this group

        :status 200: ok
        :status 400: invalid argument[s]
        :status 401: authentication required
        :status 404: group does not exist
        '''

        # Get group.
        id_ = get_int_arg('id_', id_)
        group = g.db.query(Group).filter(Group.id == id_).first()

        if group is None:
            raise NotFound("Group '%s' does not exist." % id_)

        response = group.as_dict()
        response['url-for'] = url_for('GroupView:get', id_=group.id)

        # Send response.
        return jsonify(**response)

    def post(self):
        '''
            Create a group.

            **Example Request**

            ..sourcode:: json

                {
                    "groups": [
                        {
                            "name": "gender",
                            "sites": [1, 2, 7]
                        },
                        ...
                    ]
                }

        **Example Response**

        ..sourcecode:: json

            {
                "message": "2 new groups created."
            }

        :<header Content-Type: application/json
        :<header X-Auth: the client's auth token
        :>json list groups: a list of groups to create
        :>json str groups[n].name: name of group to create

        :>header Content-Type: application/json
        :>json str message: api response message

        :status 200: created
        :status 400: invalid request body
        :status 401: authentication required
        '''

        request_json = request.get_json()
        redis = worker.get_redis()
        groups = list()

        # Validate input
        for group_json in request_json['groups']:
            validate_request_json(group_json, GROUP_ATTRS)

            try:
                request_site_ids = [int(s) for s in group_json['sites']]
            except TypeError:
                raise BadRequest('Sites must be integer site ids')

            if len(request_site_ids) == 0:
                raise BadRequest('At least one site is required.')


            sites = g.db.query(Site)\
                        .filter(Site.id.in_(request_site_ids))\
                        .all()
            site_ids = [site.id for site in sites]
            missing_sites = list(set(request_site_ids) - set(site_ids))

            if len(missing_sites) > 0:
                raise BadRequest('Site ids {} do not exist'
                                 .format(
                                     ','.join(str(s) for s in missing_sites))
                                 )

        # Create groups
        for group_json in request_json['groups']:
            try:
                group = Group(
                    name=group_json['name'].lower().strip(),
                    sites=sites
                )
                g.db.add(group)
                g.db.flush()
                groups.append(group.as_dict())
            except IntegrityError:
                g.db.rollback()
                raise BadRequest(
                    'Group "{}" already exists'.format(group.name)
                )

        # Save groups
        g.db.commit()

        # Send redis notifications
        for group in groups:
            redis.publish('group', json.dumps(group))
            # Add a link to the created group in the API json response
            group['url-for'] = url_for('GroupView:get', id_=group['id'])

        message = '{} new groups created'.format(len(request_json['groups']))
        response = jsonify(
            message=message,
            groups=groups
        )
        response.status_code = 200

        return response

    def index(self):
        '''
        Return an array of all groups.

        **Example Response**

        .. sourcecode: json

            {
                "groups": [
                    {
                        "id": 1,
                        "name": "gender",
                        "sites": [
                            {
                                "category": "books",
                                "id": 2,
                                "name": "aNobil",
                                "search_text": "- aNobii</title>",
                                "status_code": 200,
                                "url": "http://www.anobii.com/%s/books"
                            },
                            ...
                        ]
                    },
                    ...
                ],
                "total_count": 2
            }

        :<header Content-Type: application/json
        :<header X-Auth: the client's auth token
        :query page: the page number to display (default: 1)
        :query rpp: the number of results per page (default: 10)

        :>header Content-Type: application/json
        :>json list groups: a list of group objects
        :>json str groups[n].category: the group category
        :>json int groups[n].id: unique identifier for group
        :>json str groups[n].name: the group name
        :>json list groups[n].sites: list of sites associated with this group
        :>json str groups[n].sites[n].category: the site category
        :>json str groups[n].sites[n].id: the unique id for site
        :>json str groups[n].sites[n].name: the site name
        :>json str groups[n].sites[n].search_text: string search pattern
        :>json str groups[n].sites[n].status_code: server response code for site
        :>json str groups[n].sites[n].url: the site url

        :status 200: ok
        :status 400: invalid argument[s]
        :status 401: authentication required
        '''

        page, results_per_page = get_paging_arguments(request.args)
        query = g.db.query(Group)
        total_count = query.count()
        query = query.order_by(Group.name.asc()) \
                     .limit(results_per_page) \
                     .offset((page - 1) * results_per_page)

        groups = list()

        for group in query:
            data = group.as_dict()
            data['url-for'] = url_for('GroupView:get', id_=group.id)
            groups.append(data)

        return jsonify(
            groups=groups,
            total_count=total_count
        )

    def put(self, id_):
        '''
        Update the group identified by `id`.

            **Example Request**

            ..sourcode:: json

                {
                    {
                        "name": "priority sites"
                        "sites": [1,5]
                    },
                }

        **Example Response**

        ..sourcecode:: json

            {
                "id": 1,
                "name": "priority sites",
                "sites": [
                    {
                        "category": "books",
                        "id": 1,
                        "name": "aNobil",
                        "search_text": "- aNobii</title>",
                        "status_code": 200,
                        "url": "http://www.anobii.com/%s/books"
                    },
                    {
                        "category": "coding",
                        "id": 5,
                        "name": "bitbucket",
                        "search_text": "\"username\":",
                        "status_code": 200,
                        "url": "https://bitbucket.org/api/2.0/users/%s"
                    },
                    ...
                ]
            },

        :<header Content-Type: application/json
        :<header X-Auth: the client's auth token
        :>json str name: the value of the name attribute

        :>header Content-Type: application/json
        :>json int id: unique identifier for group
        :>json str name: the group name
        :>json list sites: list of sites associated with this group
        :>json str sites[n].category: the site category
        :>json str sites[n].id: the unique id for site
        :>json str sites[n].name: the site name
        :>json str sites[n].search_text: string search pattern
        :>json str sites[n].status_code: server response code for site
        :>json str sites[n].url: the site url

        :status 200: updated
        :status 400: invalid request body
        :status 401: authentication required
        '''
        editable_fields = ['name', 'sites']
        # Get group.
        id_ = get_int_arg('id_', id_)
        group = g.db.query(Group).filter(Group.id == id_).first()

        if group is None:
            raise NotFound("Group '%s' does not exist." % id_)

        request_json = request.get_json()
        redis = worker.get_redis()

        # Validate data and set attributes
        if request_json is None:
            raise BadRequest("Specify at least one editable field: {}"
                             .format(editable_fields))

        for field in request_json:
            if field not in editable_fields:
                raise BadRequest("'{}' is not one of the editable fields: {}"
                                 .format(field, editable_fields)
                                 )

        if 'name' in request_json:
            validate_json_attr('name', GROUP_ATTRS, request_json)
            group.name = request_json['name'].lower().strip()

        if 'sites' in request_json:
            try:
                request_site_ids = [int(s) for s in request_json['sites']]
            except ValueError:
                raise BadRequest('Sites must be a list of integer site ids')

            if len(request_site_ids) == 0:
                raise BadRequest('Groups must have at least one site')

            sites = g.db.query(Site).filter(Site.id.in_(request_site_ids)).all()
            site_ids = [site.id for site in sites]
            missing_sites = list(set(request_site_ids) - set(site_ids))

            if len(missing_sites) > 0:
                raise BadRequest('Site ids "{}" do not exist'
                                 .format(','.join(missing_sites)))
            else:
                group.sites = sites

        # Save the updated group
        g.db.add(group)
        try:
            g.db.commit()
        except DBAPIError as e:
            g.db.rollback()
            raise BadRequest('Database error: {}'.format(e))

        # Send redis notifications
        redis.publish('group', json.dumps(group.as_dict()))

        response = group.as_dict()
        response['url-for'] = url_for('GroupView:get', id_=group.id)

        # Send response.
        return jsonify(**response)

    def delete(self, id_):
        '''
        Delete the group identified by `id`.

        **Example Response**

        ..sourcecode:: json

            {
                "message": "Group `main` deleted",
            }

        :<header Content-Type: application/json
        :<header X-Auth: the client's auth token

        :>header Content-Type: application/json
        :>json str message: the API response message

        :status 200: deleted
        :status 400: invalid request body
        :status 401: authentication required
        :status 404: group does not exist
        '''

        # Get label.
        id_ = get_int_arg('id_', id_)
        group = g.db.query(Group).filter(Group.id == id_).first()

        if group is None:
            raise NotFound("Group '%s' does not exist." % id_)

        # Delete label
        g.db.delete(group)

        try:
            g.db.commit()
        except DBAPIError as e:
            raise BadRequest('Database error: {}'.format(e))

        # Send redis notifications
        notification = {
            'ids': [group.id],
            'status': 'deleted',
            'resource': None
        }
        g.redis.publish('group', json.dumps(notification))

        message = 'Group id "{}" deleted'.format(group.id)
        response = jsonify(message=message)
        response.status_code = 200

        return response
