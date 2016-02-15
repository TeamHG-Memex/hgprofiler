from flask import g, send_from_directory, jsonify
from flask.ext.classy import FlaskView
from werkzeug.exceptions import NotFound, BadRequest

import app.config
from app.authorization import login_required
from app.config import get_path
from app.rest import get_int_arg
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

        file_ = g.db.query(File).filter(File.id == id_).first()
        data_dir = get_path('data')
        cache_timeout = 0 if g.debug else None

        if file_ is None:
            raise NotFound('No file exists with id={}'.format(id_))

        if file_.mime == 'application/zip':
            return send_from_directory(
                data_dir,
                file_.relpath(),
                mimetype=file_.mime,
                as_attachment=True,
                attachment_filename=file_.name,
                cache_timeout=cache_timeout
            )
        else:
            return send_from_directory(
                data_dir,
                file_.relpath(),
                mimetype=file_.mime,
                cache_timeout=cache_timeout
            )

    def delete(self, id_):
        '''
        Delete file identified by `id_`.
        '''
        # Get site.
        id_ = get_int_arg('id_', id_)
        file_ = g.db.query(File).filter(File.id == id_).first()

        if file_ is None:
            raise NotFound("File '%s' does not exist." % id_)

        # Delete db file record
        try:
            g.db.delete(file_)
            g.db.commit()
        except Exception as e:
            g.db.rollback()
            raise BadRequest(e)

        message = 'File id "{}" deleted'.format(id_)
        response = jsonify(message=message)
        response.status_code = 200

        return response
