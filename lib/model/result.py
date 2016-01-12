from sqlalchemy import Column
from sqlalchemy import Boolean
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from model import Base


class Result(Base):
    ''' Data model for a job resul. '''

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
    error = Column(String(255), nullable=True)

    def __init__(self, job_id, site_name, site_url, found, number, total, error=None):
        ''' Constructor. '''

        self.job_id = job_id
        self.site_name = site_name
        self.site_url = site_url
        self.found = found
        self.number = number
        self.total = total
        self.error = error

    def as_dict(self):
        ''' Return dictionary representation of this site. '''
        return {
            'id': self.id,
            'job_id': self.job_id,
            'site_name': self.site_name,
            'site_url': self.site_url,
            'found': self.found,
            'number': self.number,
            'total': self.total,
            'error': self.error,
        }
