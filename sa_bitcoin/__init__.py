# -*- coding: utf-8 -*-

VERSION = (0,0,3, 'alpha', 0)

def get_version():
    version = '%s.%s' % (VERSION[0], VERSION[1])
    if VERSION[2]:
        version = '%s.%s' % (version, VERSION[2])
    if VERSION[3:] == ('alpha', 0):
        version = '%spre-alpha' % version
    else:
        if VERSION[3] != 'final':
            version = "%s%s" % (version, VERSION[3])
            if VERSION[4] != 0:
                version = '%s%s' % (version, VERSION[4])
    return version

# ===----------------------------------------------------------------------===

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# SQLAlchemy ORM event registration
from sqlalchemy import event, orm

@event.listens_for(orm.Session, 'before_flush')
def lazy_defaults(session, flush_context, instances):
    "Sets default values if left unspecified by the developer"
    for target in session.new.union(session.dirty):
        for attr in getattr(target, '__lazy_slots__', ()):
            # This code may look like it does nothing, but in fact we are using
            # properties to lazily generate values for some columns, so calling
            # `getattr()` evaluates those lazy expressions. This is slightly
            # kludgy.. but necessary as SQLAlchemy never calls `getattr()`
            # before passing the field values to the database layer.
            getattr(target, attr)
