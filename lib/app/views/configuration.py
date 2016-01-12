from flask import g, jsonify, request
from flask.ext.classy import FlaskView
from werkzeug.exceptions import BadRequest, NotFound

import app.config
from app.authorization import admin_required
from app.rest import url_for
from model import Configuration


class ConfigurationView(FlaskView):
    '''
    Set configuration values.

    Requires an administrator account.
    '''

    decorators = [admin_required]

    def index(self):
        '''
        List configuration key/value pairs.

        **Example Response**

        .. sourcecode:: json

            {
                "configuration": {
                    "piscina_ui_url": "https://piscina.com:8080",
                    "piscina_proxy_url": "https://piscina.com:8080",
                    ...
                }
            }

        :<header Content-Type: application/json
        :<header X-Auth: the client's auth token

        :>header Content-Type: application/json
        :>json dict configuration: a dictionary of configuration key/value
            pairs.

        :status 200: ok
        :status 401: authentication required
        :status 403: must be an administrator
        '''

        configuration = {c.key:c.value for c in g.db.query(Configuration).all()}

        return jsonify(configuration=configuration)

    def put(self, key):
        '''
        Update a configuration key/value pair.

        **Example Request**

        .. sourcecode:: json

            PUT /api/configuration/my-key
            {
                "value": "my-value"
            }

        **Example Response**

        .. sourcecode:: json

            {
                "message": "Configuration saved."
            }

        :<header Content-Type: application/json
        :<header X-Auth: the client's auth token
        :<json str value: the new value to set for the supplied key

        :>json str message: human-readable response

        :status 200: ok
        :status 401: authentication required
        :status 403: must be an administrator
        '''

        body = request.get_json()
        value = body.get('value', '').strip()

        configuration = g.db.query(Configuration) \
                            .filter(Configuration.key==key) \
                            .first()

        if configuration is None:
            raise NotFound('There is no configuration item named "{}".'.format(key))

        configuration.value = value
        g.db.commit()

        return jsonify(message='Configuration saved.')
