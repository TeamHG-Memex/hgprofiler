from sqlalchemy import (Boolean,
                        Column,
                        ForeignKey,
                        Integer,
                        String,
                        UniqueConstraint)
from sqlalchemy.orm import relationship

from model import Base
from model.file import File


class Result(Base):
    ''' Data model for a job result. '''

    __tablename__ = 'result'
    __table_args__ = (
        UniqueConstraint('job_id', 'site_url',  name='job_id_site_url'),
    )

    id = Column(Integer, primary_key=True)
    job_id = Column(String(255), nullable=False)
    site_name = Column(String(255), nullable=False)
    site_url = Column(String(255), nullable=False)
    found = Column(Boolean, default=False)
    number = Column(Integer, nullable=False)
    total = Column(Integer, nullable=False)
    image_file_id = Column(Integer, ForeignKey('file.id', name='fk_image_file'), nullable=True)
    image_file = relationship('File', primaryjoin='Result.image_file_id == File.id')
    error = Column(String(255), nullable=True)

    def __init__(self,
                 job_id,
                 site_name,
                 site_url,
                 found,
                 number,
                 total,
                 image_file_id=None,
                 thumb=None,
                 error=None):
        ''' Constructor. '''

        self.job_id = job_id
        self.site_name = site_name
        self.site_url = site_url
        self.found = found
        self.number = number
        self.total = total
        self.image_file_id = image_file_id
        self.thumb = thumb
        self.error = error

    def as_dict(self):
        ''' Return dictionary representation of this result. '''
        if self.image_file is not None:
            image_file_url = '/api/file/{}'.format(self.image_file_id)
            image_file_name = self.image_file.name
        else:
            image_file_url = None
            image_file_name = None

        return {
            'id': self.id,
            'job_id': self.job_id,
            'site_name': self.site_name,
            'site_url': self.site_url,
            'image_file_id': self.image_file_id,
            'image_file_name': image_file_name,
            'image_file_url': image_file_url,
            'found': self.found,
            'number': self.number,
            'total': self.total,
            'error': self.error,
        }
