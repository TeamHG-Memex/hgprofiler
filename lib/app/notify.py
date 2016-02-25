import json

from flask import g, request


def notify(redis, channel, message):
    '''
    Send a notification on `channel` containing `message` via the pubsub
    on `redis`.
    '''

    redis.publish(channel, json.dumps(message))


def notify_mask_client(channel, message):
    '''
    Send notification on `channel` containing message `data`.

    This function avoids sending the notification back to the client that
    initiated it.

    Note: this must be called from a flask request context. For notifications
    generated outside a request context, call notify() above and pass in a
    redis instance.
    '''

    message['source_client_id'] = request.headers.get('X-Client-Id', '')
    g.redis.publish(channel, json.dumps(message))

