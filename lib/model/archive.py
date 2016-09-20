from sqlalchemy import (DateTime,
                        Column,
                        func,
                        ForeignKey,
                        Integer,
                        String,
                        UniqueConstraint)
from sqlalchemy.orm import relationship

from model import Base


class Archive(Base):
    ''' Data model for a results archive. '''

    __tablename__ = 'archive'
    __table_args__ = (
        UniqueConstraint('tracker_id', 'zip_file_id',  name='tracker_id_zip_file_id'),
    )

    id = Column(Integer, primary_key=True)
    tracker_id = Column(String(255), nullable=False)
    username = Column(String(255), nullable=False)
    group_id = Column(Integer, ForeignKey('group.id'), nullable=True)
    date = Column(DateTime, default=func.current_timestamp())
    site_count = Column(Integer, nullable=False)
    found_count = Column(Integer, nullable=False)
    not_found_count = Column(Integer, nullable=False)
    error_count = Column(Integer, nullable=False)
    zip_file_id = Column(Integer, ForeignKey('file.id', name='fk_zip_file'))

    def __init__(self,
                 tracker_id,
                 username,
                 group_id,
                 site_count,
                 found_count,
                 not_found_count,
                 error_count,
                 zip_file_id):
        ''' Constructor. '''

        self.tracker_id = tracker_id
        self.username = username
        self.group_id = group_id
        self.site_count = site_count
        self.found_count = found_count
        self.not_found_count = not_found_count
        self.error_count = error_count
        self.zip_file_id = zip_file_id

    def as_dict(self):
        ''' Return dictionary representation of this archive. '''

        return {
            'id': self.id,
            'tracker_id': self.tracker_id,
            'username': self.username,
            'group_id': self.group_id,
            'date': self.date.isoformat(),
            'site_count': self.site_count,
            'found_count': self.found_count,
            'not_found_count': self.not_found_count,
            'error_count': self.error_count,
            'zip_file_url': '/api/file/{}'.format(self.zip_file_id),
            'zip_file_id': self.zip_file_id
        }
