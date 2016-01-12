from sqlalchemy import Column
from sqlalchemy import Boolean
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy import Enum
from model import Base
from model.site import Site


class Job(Base):
    ''' Data model for a job. '''

    __tablename__ = 'job'

    id = Column(Integer, primary_key=True)
    username = Column(String(255), nullable=False)
    status = Column(
        Enum('queued', 'scraping', 'complete', name='job_status_types')
    )

    def __init__(self, username):
        ''' Constructor. '''

        self.username = username

    def as_dict(self):
        ''' Return dictionary representation of this site. '''
        return {
            'id': self.id,
            'username': self.username,
            'status': self.status
        }
