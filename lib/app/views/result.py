import json
from flask import g, jsonify, request
from flask.ext.classy import FlaskView, route
from werkzeug.exceptions import BadRequest, NotFound
from sqlalchemy.exc import IntegrityError

import app.config
from app.authorization import login_required
from app.notify import notify_mask_client
from app.rest import (get_int_arg,
                      get_paging_arguments,
                      validate_request_json,
                      validate_json_attr)
from model import Result
import worker


class ResultView(FlaskView):
    '''
    Profiler result list.
    '''

    decorators = [login_required]

    def index(self):
        '''
        Return an array of result archives.

        **Example Response**

        .. sourcecode:: json

            {
                "results": [
                    {
                        "id": 1,
                        "job_id": '2298d96a-653d-42f2-b6d3-73ff337d51ce',
                        "site_name": "Acme",
                        "site_url": "https://www.acme.com/%s",
                        "status": "Found",
                        "number": "5",
                        "total": "166",
                        "image_file_id": "1234"
                        "error": "",
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
        :>json list results: a list of result objects
        :>json int results[n].id: the unique id of this result
        :>json str results[n].job_id: the job_id of this result
        :>json str results[n].site_name: the site name of this result
        :>json str results[n].site_url: the site URL of this result
        :>json str results[n].status: result status (Found, Not Found, Error)
        :>json str results[n].image_file_id: the file ID of the result screenshot
        :>json str results[n].error: result error message

        :status 200: ok
        :status 400: invalid argument[s]
        :status 401: authentication required
        '''

        page, results_per_page = get_paging_arguments(request.args)

        query = g.db.query(Result)

        total_count = query.count()

        query = query.limit(results_per_page) \
                     .offset((page - 1) * results_per_page)

        results = list()

        for result in query:
            results.append(result.as_dict())

        return jsonify(
            results=results,
            total_count=total_count
        )

    @route('/job/<string:job_id>')
    def get_by_job_id(self, job_id):
        '''
        Return results identified by `job_id`.

        **Example Response**

        .. sourcecode:: json

            {
                "results": [
                    {
                        "id": 1,
                        "job_id": '2298d96a-653d-42f2-b6d3-73ff337d51ce',
                        "site_name": "Acme",
                        "site_url": "https://www.acme.com/%s",
                        "status": "Found",
                        "number": "5",
                        "total": "166",
                        "image_file_id": "1234"
                        "error": "",
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
        :>json list results: a list of result objects
        :>json int results[n].id: the unique id of this result
        :>json str results[n].job_id: the job_id of this result
        :>json str results[n].site_name: the site name of this result
        :>json str results[n].site_url: the site URL of this result
        :>json str results[n].status: result status (Found, Not Found, Error)
        :>json str results[n].image_file_id: the file ID of the result screenshot
        :>json str results[n].error: result error message

        :status 200: ok
        :status 400: invalid argument[s]
        :status 401: authentication required
        '''

        page, results_per_page = get_paging_arguments(request.args)

        query = g.db.query(Result).filter(Result.job_id==job_id)

        total_count = query.count()

        query = query.limit(results_per_page) \
                     .offset((page - 1) * results_per_page)

        results = list()

        for result in query:
            results.append(result.as_dict())

        return jsonify(
            results=results,
            total_count=total_count
        )
