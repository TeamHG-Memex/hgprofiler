'''
Import all models classes in this package and expose them as members of this
module.

When this is done, you can do something like 'from model import Codename'
instead of 'from model.codename import Codename'.
'''

import importlib
import inspect
import os
import sys

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

for file_ in os.listdir(os.path.dirname(__file__)):
    name, ext = os.path.splitext(file_)

    if ext != '.py':
        continue

    package_module = importlib.import_module("%s.%s" % (__package__, name))
    for name, member in inspect.getmembers(package_module, inspect.isclass):
        if issubclass(member, Base) and member is not Base:
            setattr(sys.modules[__name__], name, member)
