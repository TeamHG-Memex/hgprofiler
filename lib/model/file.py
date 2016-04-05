import time
import random
import binascii
import hashlib
import os
import zipfile
import string

from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import BYTEA

from helper.functions import get_path
from model import Base


class File(Base):
    '''
    Data model for a file stored in the file system.

    Files are stored in a content-addressable file system: a SHA-2 hash of the
    content determines the path where it is stored. For example, a file with
    hash e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 is
    stored in
    data/e/3/b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855.

    Zip archives can be created by setting zip_archive=True and passing a list of file tuples
    and/or str_files tuples:

    zip_files = [
        ('filename.jpg','path/to/file')
    ]

    zip_str_files = [
        ('filename.csv','some,juicy,content')
    ]

    zip_str_files are created in-memory using StringIO and written as zipfile.ZipInfo.
    '''

    __tablename__ = 'file'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    mime = Column(String(255))
    hash = Column(BYTEA(32))  # sha256

    def __init__(self,
                 name,
                 mime,
                 content=None,
                 zip_archive=False,
                 zip_files=[],
                 zip_str_files=[]):
        '''
        Constructor.
        '''

        self.name = name
        self.mime = mime

        # Create dummy content to use in hash if there is no content (zip archives)
        if content is None:
            content = 'DUMMY DATA - '
            content += ''.join(random.SystemRandom()
                               .choice(string.ascii_uppercase + string.digits)
                               for _ in range(1000))
            content = content.encode('utf-8')

        hash_ = hashlib.sha256()
        hash_.update(content)
        self.hash = hash_.digest()

        # Write content to file.
        data_dir = get_path('data')
        hash_hex = binascii.hexlify(self.hash).decode('ascii')
        dir1 = os.path.join(data_dir, hash_hex[0])
        dir2 = os.path.join(dir1, hash_hex[1])
        path = os.path.join(dir2, hash_hex[2:])

        if not os.path.isdir(dir1):
            os.mkdir(dir1)

        if not os.path.isdir(dir2):
            os.mkdir(dir2)

        if not os.path.isfile(path):
            if zip_archive:
                self.zip_files(path, zip_files, zip_str_files)
            else:
                file_ = open(path, 'wb')
                file_.write(content)
                file_.close()

    def zip_files(self, path, files, str_files):
        ''' Create a zip archive of files and string files.'''

        zip_file = zipfile.ZipFile(path, 'w')
        data_dir = get_path('data')

        # Add files
        for f in files:
            f_path = os.path.join(data_dir, f[1])
            zip_file.write(f_path, arcname=f[0], compress_type=zipfile.ZIP_DEFLATED)

        # Write string files
        for str_file in str_files:
            info = zipfile.ZipInfo(str_file[0])
            info.date_time = time.localtime(time.time())[:6]
            info.compress_type = zipfile.ZIP_DEFLATED
            zip_file.writestr(info, str_file[1])

        zip_file.close()

    def relpath(self):
        ''' Return path to the file relative to the data directory. '''

        hash_ = binascii.hexlify(self.hash).decode('ascii')

        return os.path.join(hash_[0], hash_[1], hash_[2:])

    def url(self):
        '''
        Return API relative URL for file.
        '''
        return '/api/file/{}'.format(self.id)


    def as_dict(self):
        ''' Return dictionary representation of this file. '''

        return {
            'id': self.id,
            'name': self.name,
            'mime': self.mime,
            'path': self.relpath(),
            'url': '/api/file/{}'.format(self.id)
        }
