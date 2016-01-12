from datetime import datetime, timedelta

from flask import g, json, jsonify, render_template, request
from flask.ext.classy import FlaskView, route
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.exceptions import BadRequest, Unauthorized

from app.authorization import login_required
from app.rest import url_for
from model import User
from model.user import check_password


class AuthenticationFailure(Exception):
    ''' Represents an authentication failure. '''


class AuthenticationView(FlaskView):
    ''' API endpoints for performing authentication. '''

    @login_required
    def index(self):
        '''
        Return information about the current logged in user.

        **Example Response**

        .. sourcecode:: json

            {
                "email": "john.doe@corporation.com",
                "id": 201,
                "is_admin": false,
                "url": "https://quickpin/api/user/201"
            }

        :<header Content-Type: application/json
        :<header X-Auth: the client's auth token

        :>json str email: the current user's e-mail address
        :>json int id: user's unique identifier
        :>json bool is_admin: true if current user is an administrator
        :>json str url: API endpoint for data about this user
        :>header Content-Type: application/json

        :status 200: user is logged in
        :status 401: user is not logged in
        '''

        return jsonify(
            email=g.user.email,
            id=g.user.id,
            is_admin=g.user.is_admin,
            url=url_for('UserView:get', id_=g.user.id)
        )

    def post(self):
        '''
        Authenticate a user by his/her email and password.

        **Example Request**

        .. sourcecode:: json

            {
                "email": "user@company.com",
                "password": "s3cr3tP@SS"
            }

        **Example Response**

        .. sourcecode:: json

            {
                "message": "Authentication is successful.",
                "token": "2891.sajdfasdfs09dfasj298"
            }

        :<header Content-Type: application/json
        :<json str email: user's registered e-mail address
        :<json str password: user's password

        :>header Content-Type: application/json
        :>json str message: description of result (may be displayed to end user)
        :>json str token: signed authentication token

        :status 200: verified email and password
        :status 401: incorrect email or password
        '''

        request_json = request.get_json()

        try:
            user = g.db.query(User) \
                       .filter(User.email==request_json['email']) \
                       .one()

            if not check_password(request_json['password'], user.password_hash):
                raise AuthenticationFailure()

            expires = (datetime.now() + timedelta(hours=24)).isoformat()

            return jsonify(
                message='Authentication is successful.',
                token=g.sign('%d|%s' % (user.id, expires))
            )

        except KeyError:
            raise BadRequest('Email and password are required.')

        except (AuthenticationFailure, NoResultFound) as e:
            print(e)
            raise Unauthorized('Invalid e-mail or password.')
