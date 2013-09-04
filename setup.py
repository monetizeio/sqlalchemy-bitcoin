#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from distutils.core import setup

from sa_bitcoin import get_version

# Compile the list of packages available, because distutils doesn't have an
# easy way to do this.
packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir:
    os.chdir(root_dir)

for dirpath, dirnames, filenames in os.walk('sa_bitcoin'):
    # Ignore dirnames that start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith('.'): del dirnames[i]
    if '__init__.py' in filenames:
        pkg = dirpath.replace(os.path.sep, '.')
        if os.path.altsep:
            pkg = pkg.replace(os.path.altsep, '.')
        packages.append(pkg)
    elif filenames:
        prefix = dirpath[len('sa_bitcoin')+1:] # Strip "sa_bitcoin/" or "sa_bitcoin\"
        for f in filenames:
            data_files.append(os.path.join(prefix, f))

version = get_version().replace(' ', '-')
setup(name='sqlalchemy-bitcoin',
    version=version,
    description=
        u"A collection of tables and class mappings for storage and retrieval "
        u"of bitcoin protocol structures to a SQLAlchemy backing store.",
    author='RokuSigma Inc.',
    author_email='sqlalchemy-bitcoin@monetize.io',
    url='http://www.github.com/monetizeio/sqlalchemy-bitcoin/',
    download_url='http://pypi.python.org/packages/source/p/sqlalchemy-bitcoin/sqlalchemy-bitcoin-%s.tar.gz' % version,
    package_dir={'sa_bitcoin': 'sa_bitcoin'},
    packages=packages,
    package_data={'sa_bitcoin': data_files},
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Database :: Front-Ends',
        'Topic :: Office/Business :: Financial',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    install_requires=[
        'python-bitcoin>=0.0.6',
        'sqlalchemy>=0.8.2',
    ],
)

#
# End of File
#
