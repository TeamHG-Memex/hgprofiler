import base64
from datetime import datetime
import os
import re

import bcrypt
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import BYTEA

import app.config
from model import Base


class User(Base):
    ''' Data model for a user. '''

    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255))
    name = Column(String(255))
    agency = Column(String(255))
    location = Column(String(255))
    phone = Column(String(255)) # E.164 format
    thumb = Column(BYTEA)
    is_admin = Column(Boolean, default=False, nullable=False)
    created = Column(DateTime, default=datetime.now, nullable=False)
    modified = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    DEFAULT_THUMB = None

    def __init__(self, email):
        ''' Constructor. '''

        self.email = email

    def thumb_data(self):
        '''
        Get user thumbnail in base64 encoding.

        Returns a default thumbnail if this user does not have one.
        '''

        if self.thumb is None:
            if User.DEFAULT_THUMB is None:
                dir_ = app.config.get_path('static/img')
                file_ = 'default_user_thumb.png'

                with open(os.path.join(dir_, file_), 'rb') as fh:
                    User.DEFAULT_THUMB = fh.read()

            thumb_data = User.DEFAULT_THUMB
        else:
            thumb_data = self.thumb

        return base64.b64encode(thumb_data).decode('ascii')

    def thumb_data_uri(self):
        ''' Get user thumbnail as a data URI. '''

        return 'data:image/png;base64,%s' % self.thumb_data()


def check_password(password, hash_):
    ''' Check a plaintext password against a crypt-style hash. '''

    crypt_types = {
        '2a': 'bcrypt',
    }

    try:
        crypt_type = hash_.split('$')[1]
    except IndexError:
        raise ValueError("Hash is not in proper 'crypt' format: %s" % hash_)

    if crypt_types[crypt_type] == 'bcrypt':
        return bcrypt.hashpw(password, hash_) == hash_
    else:
        raise NotImplementedError("Hash algorithm is unsupported: %s" % algorithm)


def hash_password(password, algorithm, rounds):
    ''' Hash a password with a chosen algorithm and number of rounds. '''

    if algorithm == 'bcrypt':
        return bcrypt.hashpw(password, bcrypt.gensalt(rounds))
    else:
        raise NotImplementedError("Hash algorithm is unsupported: %s" % algorithm)


_LOWER_ALPHA = r'[a-z]'
_UPPER_ALPHA = r'[A-Z]'
_NUMERIC = r'[0-9]'


def valid_password(password):
    ''' Verify the password meets complexity requirements. '''

    return len(password) >= 8 and \
           re.search(_LOWER_ALPHA, password) and \
           re.search(_UPPER_ALPHA, password) and \
           re.search(_NUMERIC, password)
