import time
import json
from flask import g, request, Response
from flask.ext.classy import FlaskView
from werkzeug.exceptions import BadRequest, NotAcceptable

from app.authorization import login_required
import app.config
import app.database

import logging
logging.basicConfig(filename="/var/log/hgprofiler.log", level=logging.DEBUG)


class NotificationView(FlaskView):
    '''
    Send notifications using Server-Sent Events (SSE).

    Based on this:
    http://stackoverflow.com/questions/13386681/streaming-data-with-python-and-flask
    '''

    CHANNELS = (
        'archive',
        'group',
        'result',
        'site',
        'worker',
    )

    __should_quit = False

    @classmethod
    def quit_notifications(cls):
        '''A helper function to end long-running notification threads. '''
        cls.__should_quit = True

    @login_required
    def index(self):
        ''' Open an SSE stream. '''

        if request.headers.get('Accept') == 'text/event-stream':
            redis = app.database.get_redis(dict(g.config.items('redis')))
            pubsub = redis.pubsub(ignore_subscribe_messages=True)
            pubsub.subscribe(*self.__class__.CHANNELS)
            client_id = request.args.get('client-id', '')

            if client_id.strip() == '':
                raise BadRequest('`client-id` query parameter is required.')

            return Response(self._stream(pubsub, client_id), content_type='text/event-stream')

        else:
            message = 'This endpoint is only for use with server-sent ' \
                      'events (SSE).'
            raise NotAcceptable(message)

    def _stream(self, pubsub, client_id):
        '''
        Stream events.

        If an event has a source_client_id key set, then it is *not* sent to that client.
        '''

        # Prime the stream. (This forces headers to be sent. Otherwise the
        # client will think the stream is not open yet.)
        yield ''

        # Now send real events from the Redis pubsub channel.
        while True:
            if self.__class__.__should_quit:
                break

            message = pubsub.get_message()

            if message is not None:
                data = json.loads(message['data'].decode('utf8'))
                source_client_id = data.pop('source_client_id', '')

                if source_client_id != client_id:
                    channel = message['channel'].decode('utf8')
                    data_str = json.dumps(data)
                    yield 'event: {}\ndata: {}\n\n'.format(channel, data_str)
            else:
                time.sleep(0.2)
