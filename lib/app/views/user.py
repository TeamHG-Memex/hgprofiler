import base64
from io import BytesIO

from flask import g, json, jsonify, request, send_from_directory
from flask.ext.classy import FlaskView, route
from PIL import Image
import phonenumbers
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import BadRequest, Conflict, Forbidden, NotFound

from app.authorization import admin_required, login_required
from app.rest import get_int_arg, get_paging_arguments, url_for
from model import User
from model.user import hash_password, valid_password


class UserView(FlaskView):
    ''' API for managing users of the application. '''

    decorators = [login_required]

    def get(self, id_):
        '''
        Get the application user identified by `id`.

        **Example Response**

        .. sourcecode:: json

            {
                "agency": "Department Of Justice",
                "created": "2015-05-05T14:30:09.676268",
                "email": "john_doe@doj.gov",
                "id": 2029,
                "is_admin": true,
                "location": "Washington, DC",
                "modified": "2015-05-05T14:30:09.676294",
                "name": "Lt. John Doe",
                "phone": "+12025551234",
                "thumb": "iVBORw0KGgoAAAANS...",
                "url": "https://quickpin/api/user/2029"
            }

        :<header Content-Type: application/json
        :<header X-Auth: the client's auth token

        :>header Content-Type: application/json
        :>json str agency: the name of the organization/agency that this person
            is affiliated with (default: null)
        :>json str created: record creation timestamp in ISO-8601 format
        :>json str email: e-mail address
        :>json bool is_admin: true if this user has admin privileges, false
            otherwise
        :>json str location: location name, e.g. city or state (default: null)
        :>json str modified: record modification timestamp in ISO-8601 format
        :>json str name: user's full name, optionally including title or other
            salutation information (default: null)
        :>json str phone: phone number
        :>json str phone_e164: phone number in E.164 format
        :>json str thumb: PNG thumbnail for this user, base64 encoded
        :>json str url: url to view data about this user

        :status 200: ok
        :status 401: authentication required
        :status 404: user does not exist
        '''

        id_ = get_int_arg('id_', id_)
        user = g.db.query(User).filter(User.id == id_).first()

        if user is None:
            raise NotFound("User '%d' does not exist." % id_)

        return jsonify(**self._user_dict(user))

    def index(self):
        '''
        Return an array of data about application users.

        **Example Response**

        .. sourcecode:: json

            {
                "total_count": 2,
                "users": [
                    {
                        "agency": "Department Of Justice",
                        "created": "2015-05-05T14:30:09.676268",
                        "email": "john_doe@doj.gov",
                        "id": 2029,
                        "is_admin": true,
                        "location": "Washington, DC",
                        "modified": "2015-05-05T14:30:09.676294",
                        "name": "Lt. John Doe",
                        "phone": "+12025551234",
                        "thumb": "iVBORw0KGgo…",
                        "url": "https://quickpin/api/user/2029"
                    },
                    ...
                ]
            }

        :<header Content-Type: application/json
        :<header X-Auth: the client's auth token
        :query page: the page number to display (default: 1)
        :query rpp: the number of results per page (default: 10)

        :>header Content-Type: application/json
        :>json int total_count: the total number of application users (not just
            the ones on the current page)
        :>json list users: list of users
        :>json str users[n].agency: the name of the organization/agency that
            this person is affiliated with (default: null)
        :>json str users[n].created: record creation timestamp in ISO-8601
            format
        :>json str users[n].email: e-mail address
        :>json bool users[n].is_admin: true if this user has admin privileges,
            false otherwise
        :>json str users[n].location: location name, e.g. city or state
            (default: null)
        :>json str users[n].modified: record modification timestamp in ISO-8601
            format
        :>json str users[n].name: user's full name, optionally including title
            or other salutation information (default: null)
        :>json str users[n].phone: phone number
        :>json str thumb: PNG thumbnail for this user, base64 encoded
        :>json str users[n].url: url to view data about this user

        :status 200: ok
        :status 400: invalid argument[s]
        :status 401: authentication required
        '''

        page, results_per_page = get_paging_arguments(request.args)

        total_count = g.db.query(func.count(User.id)).scalar()
        user_query = g.db.query(User) \
                         .order_by(User.email) \
                         .limit(results_per_page) \
                         .offset((page - 1) * results_per_page)

        users = [self._user_dict(u) for u in user_query]
        return jsonify(users=users, total_count=total_count)

    @admin_required
    def post(self):
        '''
        Create a new application user.

        **Example Request**

        .. sourcecode:: json

            {
                "email": "john_doe@doj.gov",
                "password": "superSECRET123"
            }

        **Example Response**

        .. sourcecode:: json

            {
                "agency": null,
                "created": "2015-05-05T14:30:09.676268",
                "email": "john_doe@doj.gov",
                "id": 2029,
                "is_admin": false,
                "location": null,
                "modified": "2015-05-05T14:30:09.676294",
                "name": null,
                "phone": null,
                "thumb": null,
                "url": "https://quickpin/api/user/2029"
            }

        :<header Content-Type: application/json
        :<header X-Auth: the client's auth token
        :>json str email: e-mail address
        :>json str password: new password, must be >=8 characters, mixed case,

        :>header Content-Type: application/json
        :>json str agency: the name of the organization/agency that this person
            is affiliated with (default: null)
        :>json str created: record creation timestamp in ISO-8601 format
        :>json str email: e-mail address
        :>json bool is_admin: true if this user has admin privileges, false
            otherwise
        :>json str location: location name, e.g. city or state (default: null)
        :>json str modified: record modification timestamp in ISO-8601 format
        :>json str name: user's full name, optionally including title or other
            salutation information (default: null)
        :>json str phone: phone number
        :>json str phone_e164: phone number in E.164 format
        :>json str thumb: PNG thumbnail for this user, base64 encoded
        :>json str url: url to view data about this user

        :status 200: ok
        :status 400: invalid request body
        :status 401: authentication required
        :status 403: not authorized to create accounts
        :status 409: e-mail address already in use
        '''

        request_json = request.get_json()

        if 'email' not in request_json or '@' not in request_json['email']:
            raise BadRequest('Invalid or missing email.')

        user = User(request_json['email'].strip())

        if 'password' not in request_json:
            raise BadRequest('Password is required')

        password = request_json['password'].strip()

        if not valid_password(password):
            raise BadRequest('Password does not meet complexity requirements.')

        user.password_hash = hash_password(
            password,
            g.config.get('password_hash', 'algorithm'),
            int(g.config.get('password_hash', 'rounds'))
        )

        try:
            g.db.add(user)
            g.db.commit()
        except IntegrityError:
            raise Conflict('This e-mail address is already in use.')

        g.db.expire(user)

        return jsonify(**self._user_dict(user))

    def put(self, id_):
        '''
        Update data about the application identified by `id`. Omitted fields
        are not changed.

        **Example Request**

        .. sourcecode:: json

            {
                "agency": "Department Of Justice",
                "email": "john_doe@doj.gov",
                "is_admin": true,
                "location": "Washington, DC",
                "name": "Lt. John Doe",
                "password": "superSECRET123",
                "phone": "+12025551234",
                "thumb": "iVBORw0KGgoAAAANS..."
            }

        **Example Response**

        .. sourcecode:: json

            {
                "agency": "Department Of Justice",
                "created": "2015-05-05T14:30:09.676268",
                "email": "john_doe@doj.gov",
                "id": 2029,
                "is_admin": true,
                "location": "Washington, DC",
                "modified": "2015-05-05T14:30:09.676294",
                "name": "Lt. John Doe",
                "phone": "202-555-1234",
                "thumb": "iVBORw0KGgoAAAANS...",
                "url": "https://quickpin/api/user/2029"
            }

        :<header Content-Type: application/json
        :<header X-Auth: the client's auth token
        :>json str agency: the name of the organization/agency that this person
            is affiliated with
        :>json str email: e-mail address
        :>json bool is_admin: true if this user should have admin privileges,
            false otherwise (this field can only be modified by an admin user)
        :>json str location: location name, e.g. city or state (default: null)
        :>json str name: user's full name, optionally including title or other
            salutation information (default: null)
        :>json str password: new password, must be >=8 characters, mixed case,
            and contain numbers
        :>json str phone: phone number (any reasonable format is okay)
        :>json str thumb: PNG thumbnail for this user, base64 encoded

        :>header Content-Type: application/json
        :>json str agency: the name of the organization/agency that this person
            is affiliated with (default: null)
        :>json str created: record creation timestamp in ISO-8601 format
        :>json str email: e-mail address
        :>json bool is_admin: true if this user has admin privileges, false
            otherwise
        :>json str location: location name, e.g. city or state (default: null)
        :>json str modified: record modification timestamp in ISO-8601 format
        :>json str name: user's full name, optionally including title or other
            salutation information (default: null)
        :>json str phone: phone number
        :>json str phone_e164: phone number in E.164 format
        :>json str thumb: PNG thumbnail for this user, base64 encoded
        :>json str url: url to view data about this user

        :status 200: ok
        :status 400: invalid request body
        :status 401: authentication required
        :status 403: not authorized to make the requested changes
        '''

        request_json = request.get_json()
        user = g.db.query(User).filter(User.id == id_).first()

        if not g.user.is_admin and g.user.id != user.id:
            raise Forbidden('You may only modify your own profile.')

        if 'is_admin' in request_json:
            if not g.user.is_admin:
                raise Forbidden('Only admins can change user roles.')

            if g.user.id == int(id_):
                raise BadRequest('You may not modify your own role.')

            user.is_admin = request_json['is_admin']

        self._update_string_field(request_json, 'agency', user, 'agency')
        self._update_string_field(request_json, 'location', user, 'location')
        self._update_string_field(request_json, 'name', user, 'name')

        if 'email' in request_json:
            email = request_json['email'].strip()

            if email == '':
                raise BadRequest('E-mail may not be blank.')

            if '@' not in email and email != 'admin':
                raise BadRequest('Invalid e-mail address.')

            user.email = email

        if 'phone' in request_json:
            if request_json['phone'].strip() == '':
                user.phone = None
            else:
                try:
                    phone = phonenumbers.parse(request_json['phone'], 'US')

                    if not phonenumbers.is_valid_number(phone):
                        raise ValueError()
                except:
                    raise BadRequest('Invalid phone number.')

                user.phone = phonenumbers.format_number(
                    phone,
                    phonenumbers.PhoneNumberFormat.E164
                )

        if 'thumb' in request_json:
            try:
                img_data = base64.b64decode(request_json['thumb'])
                img = Image.open(BytesIO(img_data))

                if img.format != 'PNG':# or img.size != (32,32):
                    raise ValueError()
            except:
                raise BadRequest('Thumbnail image must be 32x32 px,' \
                                 ' PNG format, base64 encoded.')

            user.thumb = img_data

        if 'password' in request_json:
            password = request_json['password'].strip()

            if not valid_password(password):
                raise BadRequest('Password does not meet complexity requirements.')

            user.password_hash = hash_password(
                password,
                g.config.get('password_hash', 'algorithm'),
                int(g.config.get('password_hash', 'rounds'))
            )

        g.db.commit()
        g.db.expire(user)

        return jsonify(**self._user_dict(user))

    def _user_dict(self, user):
        ''' Populate a dictionary of user attributes. '''

        if user.phone is not None:
            phone = phonenumbers.parse(user.phone)
            pretty_phone = phonenumbers.format_number(
                phone,
                phonenumbers.PhoneNumberFormat.INTERNATIONAL
            )
        else:
            pretty_phone = None

        return {
            'agency': user.agency,
            'created': user.created.isoformat(),
            'email': user.email,
            'id': user.id,
            'is_admin': user.is_admin,
            'location': user.location,
            'modified': user.modified.isoformat(),
            'name': user.name,
            'phone_e164': user.phone,
            'phone': pretty_phone,
            'thumb': user.thumb_data(),
        }

    def _update_string_field(self, request, request_field, model, model_field):
        ''' Update a string on the model from the request. '''

        if request_field in request:
            value = request[request_field].strip()

            if value == '':
                value = None

            setattr(model, model_field, value)
