from flask import g, jsonify, request
from flask.ext.classy import FlaskView
from werkzeug.exceptions import BadRequest, NotFound

import app.config
import app.queue
from app.authorization import login_required
from app.rest import validate_request_json, validate_json_attr
from helper.functions import random_string
from model import Group, Site


USERNAME_ATTRS = {
    'usernames': {'type': list, 'required': True},
    'group': {'type': int, 'required': False},
}


class UsernameView(FlaskView):
    '''
    Search and retrieve usernames from the web using background workers.
    '''

    decorators = [login_required]

    def post(self):
        '''
        Request search of usernames.

        **Example Request**

        .. sourcecode:: json

            {
                "usernames": [
                    "johndoe",
                    "janedoe",
                    ...
                ],
                "group": 3
            }

        **Example Response**

        .. sourcecode:: json

            {
                "jobs": [
                    {
                        "id": "1",
                        "username": "johndoe",
                    },
                ]
            }

        :<header Content-Type: application/json
        :<header X-Auth: the client's auth token
        :>json list usernames: a list of usernames to search for
        :>json int group: ID of site group to use (optional)

        :>header Content-Type: application/json
        :>json list jobs: list of worker jobs
        :>json list jobs[n].id: unique id of this job
        :>json list jobs[n].usename: username target of this job

        :status 202: accepted for background processing
        :status 400: invalid request body
        :status 401: authentication required
        '''
        request_json = request.get_json()
        tracker_ids = dict()
        redis = g.redis
        group = None
        group_id = None
        jobs = []

        if 'usernames' not in request_json:
            raise BadRequest('`usernames` is required')

        validate_request_json(request_json, USERNAME_ATTRS)

        if len(request_json['usernames']) == 0:
            raise BadRequest('At least one username is required')

        if 'group' in request_json:
            group_id = request_json['group']
            group = g.db.query(Group).filter(Group.id == group_id).first()

            if group is None:
                raise NotFound("Group '%s' does not exist." % group_id)
            else:
                group_id = group.id

        if group is None:
            sites = g.db.query(Site).all()
        else:
            sites = group.sites

        for username in request_json['usernames']:
            # Create an object in redis to track the number of sites completed
            # in this search.
            tracker_id = 'tracker.{}'.format(random_string(10))
            tracker_ids[username] = tracker_id
            redis.set(tracker_id, 0)
            redis.expire(tracker_id, 600)
            total = len(sites)

            # Queue a job for each site.
            for site in sites:
                job_id = app.queue.schedule_username(
                    username, site, group_id, total, tracker_id
                )
                jobs.append({
                    'id': job_id,
                    'username': username,
                    'group': group_id
                })

        response = jsonify(tracker_ids=tracker_ids)
        response.status_code = 202

        return response
