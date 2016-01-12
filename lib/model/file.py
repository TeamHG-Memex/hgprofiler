import base64
import binascii
import hashlib
import os

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.orm import relationship

import app.config
from model import Base


class File(Base):
    '''
    Data model for a file stored in the file system.

    Files are stored in a content-addressable file system: a SHA-2 hash of the
    content determines the path where it is stored. For example, a file with
    hash e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 is
    stored in
    data/e/3/b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855.
    '''

    __tablename__ = 'file'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    mime = Column(String(255))
    hash = Column(BYTEA(32)) # sha256

    def __init__(self, name, mime, content):
        ''' Constructor. '''

        self.name = name
        self.mime = mime

        hash_ = hashlib.sha256()
        hash_.update(content)
        self.hash = hash_.digest()

        # Write content to file.
        data_dir = app.config.get_path('data')
        hash_hex = binascii.hexlify(self.hash).decode('ascii')
        dir1 = os.path.join(data_dir, hash_hex[0])
        dir2 = os.path.join(dir1, hash_hex[1])
        path = os.path.join(dir2, hash_hex[2:])

        if not os.path.isdir(dir1):
            os.mkdir(dir1)

        if not os.path.isdir(dir2):
            os.mkdir(dir2)

        if not os.path.isfile(path):
            file_ = open(path, 'wb')
            file_.write(content)
            file_.close()

    def relpath(self):
        ''' Return path to the file relative to the data directory. '''

        data_dir = app.config.get_path('data')
        hash_ = binascii.hexlify(self.hash).decode('ascii')

        return os.path.join(hash_[0], hash_[1], hash_[2:])
