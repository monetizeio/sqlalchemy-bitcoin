# -*- coding: utf-8 -*-
# Copyright © 2012-2013, RokuSigma Inc. as an unpublished work.
# Proprietary property and company confidential: all rights reserved.
# See COPYRIGHT for details.
"""\
Add user/role authentication tables for use by Flask-Security.

Revision ID: 3ee5aea862dd
Revises: None
Create Date: 2013-11-14 12:43:28.272695

"""

# revision identifiers, used by Alembic.
revision = '3ee5aea862dd'
down_revision = None

from alembic import op
from sqlalchemy import *
from sqlalchemy.sql import expression

from apps.tools.db.types import UUID

__app_label__ = 'auth'

def upgrade():
    # Role
    __tablename__ = '%s_%s' % (__app_label__, 'role')
    op.create_table(__tablename__,
        Column('uuid', UUID, server_default=func.uuid_generate_v4()),
        Column('title', String(96), nullable=False),
        PrimaryKeyConstraint('uuid',
            name = '__'.join(['pk', __tablename__])),)
    op.create_unique_constraint(
        '__'.join(['uq', __tablename__, 'title']),
                         __tablename__,('title',))

    # User
    __tablename__ = '%s_%s' % (__app_label__, 'user')
    op.create_table(__tablename__,
        Column('uuid', UUID, server_default=func.uuid_generate_v4()),
        Column('login', String(48), nullable=False),
        Column('password', String(255), server_default=u'', nullable=False),
        Column('name', String(255), server_default=u'', nullable=False),
        Column('active', Boolean, server_default=expression.false(), nullable=False),
        Column('confirmed_at', DateTime, nullable=True),
        PrimaryKeyConstraint('uuid',
            name = '__'.join(['pk', __tablename__])),)
    op.create_unique_constraint(
        '__'.join(['uq', __tablename__, 'login']),
                         __tablename__,('login',))

    # Email
    __tablename__ = '%s_%s' % (__app_label__, 'email')
    op.create_table(__tablename__,
        Column('address', String(255), nullable=False),
        Column('user_uuid', UUID, nullable=False),
        Column('notification', Boolean,
            server_default = expression.true(),
            nullable       = False),
        Column('secure_reset', Boolean,
            server_default = expression.true(),
            nullable       = False),
        PrimaryKeyConstraint('address',
            name = '__'.join(['pk', __tablename__])),)
    op.create_foreign_key(
        '__'.join(['fk', __tablename__, 'user']),
                         __tablename__,
        '%s_%s' % (__app_label__, 'user'),
        ('user_uuid',),
        (     'uuid',))
    op.create_index(
        '__'.join(['ix', __tablename__, 'user_uuid']),
                         __tablename__,
        ('user_uuid',))
    op.create_index(
        '__'.join(['ix', __tablename__, 'notification']),
                         __tablename__,
        ('notification',))

    # UserRole
    __tablename__ = '%s_%s' % (__app_label__, 'user_role')
    op.create_table(__tablename__,
        Column('user_uuid', UUID, nullable=False),
        Column('role_uuid', UUID, nullable=False),
        PrimaryKeyConstraint('user_uuid', 'role_uuid',
            name = '__'.join(['pk', __tablename__])),)
    op.create_foreign_key(
        '__'.join(['fk', __tablename__, 'role']),
                         __tablename__,
        '%s_%s' % (__app_label__, 'role'),
        ('role_uuid',),
        (     'uuid',))
    op.create_foreign_key(
        '__'.join(['fk', __tablename__, 'user']),
                         __tablename__,
        '%s_%s' % (__app_label__, 'user'),
        ('user_uuid',),
        (     'uuid',))

def downgrade():
    # UserRole
    __tablename__ = '%s_%s' % (__app_label__, 'user_role')
    op.drop_constraint('__'.join(['fk', __tablename__, 'user']),
                                        __tablename__, type_='foreignkey')
    op.drop_constraint('__'.join(['fk', __tablename__, 'role']),
                                        __tablename__, type_='foreignkey')
    op.drop_table(__tablename__)

    # Email
    __tablename__ = '%s_%s' % (__app_label__, 'email')
    op.drop_index('__'.join(['ix', __tablename__, 'notification']),
                                   __tablename__)
    op.drop_index('__'.join(['ix', __tablename__, 'user_uuid']),
                                   __tablename__)
    op.drop_constraint('__'.join(['fk', __tablename__, 'user']),
                                        __tablename__, type_='foreignkey')
    op.drop_table(__tablename__)

    # User
    __tablename__ = '%s_%s' % (__app_label__, 'user')
    op.drop_constraint('__'.join(['uq', __tablename__, 'login']),
                                        __tablename__, type_='unique')
    op.drop_table(__tablename__)

    # Role
    __tablename__ = '%s_%s' % (__app_label__, 'role')
    op.drop_constraint('__'.join(['uq', __tablename__, 'title']),
                                        __tablename__, type_='unique')
    op.drop_table(__tablename__)
