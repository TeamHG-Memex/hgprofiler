from flask import jsonify
from flask.ext.classy import FlaskView

from app.rest import url_for


class ApiIndexView(FlaskView):
    ''' API for data about users on dark web sites. '''

    def index(self):
        '''
        Provide links to sections of the API.

        **Example Response**

        .. sourcecode:: json

            {
                "authentication_url": "https://quickpin/api/authentication/",
                "dark_user_url": "https://quickpin/api/search/"
            }

        :<header Content-Type: application/json

        :>header Content-Type: application/json

        :status 200: user is logged in
        '''

        return jsonify(
            authentication_url=url_for('AuthenticationView:index'),
            search_url=url_for('SearchView:index')
        )
