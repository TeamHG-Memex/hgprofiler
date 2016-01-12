from flask import jsonify, request
from flask.ext.classy import FlaskView
from werkzeug.exceptions import BadRequest

import app.config
import app.queue
from app.authorization import login_required


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
                ]
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

        :>header Content-Type: application/json
        :>json list jobs: list of worker jobs
        :>json list jobs[n].id: unique id of this job
        :>json list jobs[n].usename: username target of this job

        :status 202: accepted for background processing
        :status 400: invalid request body
        :status 401: authentication required
        '''
        request_json = request.get_json()
        jobs = []

        for username in request_json['usernames']:
            if username.strip() == '':
                raise BadRequest('Username requires at least one character.')

        for username in request_json['usernames']:
            job_id = app.queue.schedule_username(username)
            jobs.append({'id': job_id, 'username': username})

        response = jsonify(jobs=jobs)
        response.status_code = 202

        return response
