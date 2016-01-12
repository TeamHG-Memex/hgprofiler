from sqlalchemy import Column, Integer, String, UniqueConstraint
from model import Base


class Site(Base):
    ''' Data model for a profile. '''

    __tablename__ = 'site'
    __table_args__ = (
        UniqueConstraint('url', name='site_url'),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    url = Column(String(255), nullable=False)
    category = Column(String(255), nullable=False)
    status_code = Column(Integer, nullable=True)
    search_text = Column(String(255), nullable=True)

    def __init__(self, name, url, category, status_code=None,  search_text=None):
        ''' Constructor. '''

        self.name = name
        self.url = url
        self.category = category
        self.status_code = status_code
        self.search_text = search_text

    def as_dict(self):
        ''' Return dictionary representation of this site. '''
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'category': self.category,
            'status_code': self.status_code,
            'search_text': self.search_text,
        }
