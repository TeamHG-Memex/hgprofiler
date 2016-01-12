from flask import g, send_from_directory
from flask.ext.classy import FlaskView
from werkzeug.exceptions import NotFound

import app.config
from app.authorization import login_required
from app.rest import url_for
from model import File


class FileView(FlaskView):
    ''' Manipulate files. '''

    decorators = [login_required]

    def get(self, id_):
        '''
        Get a file identified by ``id_``.

        :status 200: ok
        :status 401: authentication required
        :status 404: no file with that ID
        '''

        file_ = g.db.query(File).filter(File.id==id_).first()
        data_dir = app.config.get_path('data')
        cache_timeout = 0 if g.debug else None

        if file_ is None:
            raise NotFound('No file exists with id={}'.format(id_))

        return send_from_directory(
            data_dir,
            file_.relpath(),
            mimetype=file_.mime,
            cache_timeout=cache_timeout
        )
