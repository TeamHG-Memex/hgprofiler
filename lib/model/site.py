from sqlalchemy import (Boolean,
                        Column,
                        DateTime,
                        ForeignKey,
                        Integer,
                        String,
                        UniqueConstraint)
from sqlalchemy.orm import relationship

from model import Base
from helper.functions import random_string


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
    test_username_pos = Column(String(255), nullable=False)
    test_username_neg = Column(String(255), nullable=False)
    test_result_pos_id = Column(Integer,
                                ForeignKey('result.id',
                                           name='fk_pos_result'),
                                nullable=True)
    test_result_pos = relationship('Result',
                                   lazy='joined',
                                   backref='site_pos_result',
                                   foreign_keys='Site.test_result_pos_id',
                                   uselist=False,
                                   cascade='all')
    test_result_neg_id = Column(Integer,
                                ForeignKey('result.id',
                                           name='fk_neg_result'),
                                nullable=True)
    test_result_neg = relationship('Result',
                                   lazy='joined',
                                   backref='site_neg_result',
                                   foreign_keys='Site.test_result_neg_id',
                                   uselist=False,
                                   cascade='all')
    tested_at = Column(DateTime, nullable=True)
    valid = Column(Boolean, nullable=False, default=False)

    def __init__(self, name, url, category, test_username_pos,
                 status_code=None, search_text=None, test_username_neg=None):
        ''' Constructor. '''

        self.name = name
        self.url = url
        self.category = category
        self.status_code = status_code
        self.search_text = search_text
        self.test_username_pos = test_username_pos

        if not test_username_neg:
            self.test_username_neg = random_string(16)

    def as_dict(self):
        ''' Return dictionary representation of this site. '''

        # Preformat..
        if self.tested_at:
            tested_at = self.tested_at.isoformat()
        else:
            tested_at = None

        if self.test_result_pos:
            test_result_pos = self.test_result_pos.as_dict()
        else:
            test_result_pos = None

        if self.test_result_neg:
            test_result_neg = self.test_result_neg.as_dict()
        else:
            test_result_neg = None

        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'category': self.category,
            'status_code': self.status_code,
            'search_text': self.search_text,
            'test_username_pos': self.test_username_pos,
            'test_username_neg': self.test_username_neg,
            'test_result_pos': test_result_pos,
            'test_result_neg': test_result_neg,
            'tested_at': tested_at,
            'valid': self.valid,
        }
