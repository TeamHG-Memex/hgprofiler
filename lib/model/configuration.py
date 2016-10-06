from sqlalchemy import Column, Integer, String, Text

from model import Base


class Configuration(Base):
    '''
    Stores a configuration key/value pair.
    '''

    __tablename__ = 'configuration'

    id = Column(Integer, primary_key=True)
    key = Column(String(255), unique=True)
    value = Column(Text)

    def __init__(self, key, value):
        ''' Constructor. '''

        self.key = key
        self.value = value


def get_config(session, key, required=False):
    ''' Get a configuration value from the database. '''

    result = session.query(Configuration) \
                    .filter(Configuration.key == key) \
                    .one()

    if required and result.value == '':
        raise ValueError('(Configuration) {} cannot be blank.'.format(key))

    return result
