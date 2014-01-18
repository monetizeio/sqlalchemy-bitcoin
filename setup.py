#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.md')).read()
CHANGES = open(os.path.join(here, 'CHANGES.md')).read()
requires = filter(lambda r:'libs/' not in r,
    open(os.path.join(here, 'requirements.txt')).read().split())
packages = filter(lambda p:not p.startswith('xunit'), find_packages())

version = '0.0.3pre-alpha'
setup(**{
    'name': 'sqlalchemy-bitcoin',
    'version': version,
    'description': 
        u"A collection of tables and class mappings for storage and retrieval "
        u"of bitcoin protocol structures to a SQLAlchemy backing store.",
    'long_description': README + '\n\n' + CHANGES,
    'author':       'Monetize.io Inc.',
    'author_email': 'support@tradecraft.io',
    'url':          'https://tradecraft.io/',
    'download_url': 'http://pypi.python.org/packages/source/p/sqlalchemy-bitcoin/sqlalchemy-bitcoin-%s.tar.gz' % version,
    'packages': packages,
    'classifiers': [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Database :: Front-Ends',
        'Topic :: Office/Business :: Financial',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    'install_requires': requires,
})
