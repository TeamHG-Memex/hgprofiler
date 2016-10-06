from flask import g, jsonify, request
from flask.ext.classy import FlaskView
from werkzeug.exceptions import BadRequest, NotFound

import app.config
import app.queue
from app.authorization import login_required
from app.rest import validate_request_json
from helper.functions import random_string
from model import Group, Site


USERNAME_ATTRS = {
    'usernames': {'type': list, 'required': True},
    'group': {'type': int, 'required': False},
    'site': {'type': int, 'required': False},
    'test': {'type': bool, 'required': False},
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
                "group": 3,
                "test": False,
            }

        **Example Response**

        .. sourcecode:: json

            {
                "tracker_ids": {
                        "johndoe": "tracker.12344565",
                }
                
            }

        :<header Content-Type: application/json
        :<header X-Auth: the client's auth token
        :>json list usernames: a list of usernames to search for
        :>json int group: ID of site group to use (optional)
        :>json int site: ID of site to search (optional)
        :>json bool test: test results (optional, default: false)

        :>header Content-Type: application/json
        :>json list jobs: list of worker jobs
        :>json list jobs[n].id: unique id of this job
        :>json list jobs[n].usename: username target of this job

        :status 202: accepted for background processing
        :status 400: invalid request body
        :status 401: authentication required
        '''
        test = False
        group = None
        group_id = None
        jobs = []
        tracker_ids = dict()
        redis = g.redis
        request_json = request.get_json()
        site = None

        if 'usernames' not in request_json:
            raise BadRequest('`usernames` is required')

        validate_request_json(request_json, USERNAME_ATTRS)

        if len(request_json['usernames']) == 0:
            raise BadRequest('At least one username is required')

        if 'group' in request_json and 'site' in request_json:
            raise BadRequest('Supply either `group` or `site`.')

        if 'group' in request_json:
            group_id = request_json['group']
            group = g.db.query(Group).filter(Group.id == group_id).first()

            if group is None:
                raise NotFound("Group '%s' does not exist." % group_id)
            else:
                group_id = group.id

        if 'site' in request_json:
            site_id = request_json['site']
            site = g.db.query(Site).filter(Site.id == site_id).first()

            if site is None:
                raise NotFound("Site '%s' does not exist." % site_id)

        if 'test' in request_json:
            test = request_json['test']

        if group:
            sites = group.sites
        elif site:
            sites = g.db.query(Site).filter(Site.id == site.id).all()
        else:
            sites = g.db.query(Site).all()

        # Only query valid sites. 
        sites = sites.filter(valid==True)

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
                    username=username,
                    site=site,
                    group_id=group_id,
                    total=total,
                    tracker_id=tracker_id,
                    test=test
                )
                jobs.append({
                    'id': job_id,
                    'username': username,
                    'group': group_id,
                })

        response = jsonify(tracker_ids=tracker_ids)
        response.status_code = 202

        return response
