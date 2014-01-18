# -*- coding: utf-8 -*-
# Copyright © 2013 by its contributors. See AUTHORS for details.
# Distributed under the MIT/X11 software license, see the accompanying
# file LICENSE or http://www.opensource.org/licenses/mit-license.php.

"""\
Create core bitcoin data structures.

Revision ID: 221200742ae7
Revises: None
Create Date: 2014-01-13 10:50:12.852057
"""

# revision identifiers, used by Alembic.
revision = '221200742ae7'
down_revision = None

from alembic import op
from sqlalchemy import *

__tableprefix__ = 'bitcoin_'

def upgrade():
    # Chain
    __tablename__ = __tableprefix__ + 'chain'
    op.create_table(__tablename__,
        Column('id', Integer,
            Sequence('__'.join(['sq', __tablename__, 'id'])),
            nullable = False),
        Column('magic', LargeBinary(4), nullable=False),
        Column('port', UnsignedSmallInteger, nullable=False),
        Column('genesis', LargeBinary(80), nullable=False),
        Column('genesis_hash', Hash256, nullable=False),
        Column('pubkey_hash_prefix', SmallInteger, nullable=False),
        Column('script_hash_prefix', SmallInteger, nullable=False),
        Column('secret_prefix', SmallInteger, nullable=False),
        Column('is_testnet', Boolean, nullable=False),
        PrimaryKeyConstraint('id',
            name = '__'.join(['pk', __tablename__])),
        CheckConstraint(sql.column('port') != 0,
            name = '__'.join(['ck', __tablename__, 'port'])),
        UniqueConstraint('genesis',
            name = '__'.join(['uq', __tablename__, 'genesis'])),
        Index('__'.join(['ix', __tablename__, 'genesis_hash']),
            'genesis_hash', unique = True),
        CheckConstraint(
            (0 <= sql.column('pubkey_hash_prefix')) & (sql.column('pubkey_hash_prefix') <= 255) &
            (0 <= sql.column('script_hash_prefix')) & (sql.column('script_hash_prefix') <= 255) &
            (0 <= sql.column(     'secret_prefix')) & (sql.column(     'secret_prefix') <= 255) &
            (sql.column('pubkey_hash_prefix') != sql.column('script_hash_prefix')) &
            (sql.column('script_hash_prefix') != sql.column('secret_prefix')) &
            (sql.column('pubkey_hash_prefix') != sql.column('secret_prefix')),
            name = '__'.join(['ck', __tablename__, 'prefix'])),)

    # Checkpoint
    __tablename__ = __tableprefix__ + 'checkpoint'
    op.create_table(__tablename__,
        Column('chain_id', Integer,
            ForeignKey(__tableprefix__ + 'chain.id',
                name = '__'.join(['fk', __tablename__, 'chain'])),
            nullable = False),
        Column('height', Integer, nullable=False),
        Column('hash', Hash256, nullable=False),
        PrimaryKeyConstraint('chain_id', 'height',
            name = '__'.join(['pk', __tablename__])),
        CheckConstraint(0 <= sql.column('height'),
            name = '__'.join(['ck', __tablename__, 'height'])),)

    # Block
    __tablename__ = __tableprefix__ + 'block'
    op.create_table(__tablename__,
        Column('id', Integer,
            Sequence('__'.join(['sq', __tablename__, 'id'])),
            nullable = False),
        Column('format', SmallInteger, nullable=False),
        Column('version', UnsignedInteger, nullable=False),
        Column('parent_hash', Hash256, nullable=False),
        Column('merkle_hash', Hash256, nullable=False),
        Column('time', UNIXDateTime, nullable=False),
        Column('bits', Integer, nullable=False),
        Column('nonce', UnsignedInteger, nullable=False),
        Column('hash', Hash256, nullable=False),
        PrimaryKeyConstraint('id',
            name = '__'.join(['pk', __tablename__])),
        Index('__'.join(['ix', __tablename__, 'hash']),
            'hash', unique = True),
        CheckConstraint(
            (16842752 <= sql.column('bits')) & (sql.column('bits') <= 486604799),
            name = '__'.join(['ck', __tablename__, 'bits'])),)

    # Transaction
    __tablename__ = __tableprefix__ + 'transaction'
    op.create_table(__tablename__,
        Column('id', Integer,
            Sequence('__'.join(['sq', __tablename__, 'id'])),
            nullable = False),
        Column('format', SmallInteger, nullable=False),
        Column('version', UnsignedInteger, nullable=False),
        Column('lock_time', BlockTime, nullable=False),
        Column('reference_height', UnsignedInteger, nullable=False),
        Column('hash', Hash256, nullable=False),
        PrimaryKeyConstraint('id',
            name = '__'.join(['pk', __tablename__])),
        Index('__'.join(['ix', __tablename__, 'hash']),
            'hash', unique = True),)

    # Output
    __tablename__ = __tableprefix__ + 'output'
    op.create_table(__tablename__,
        Column('transaction_id', Integer,
            ForeignKey(__tableprefix__ + 'transaction.id',
                name = '__'.join(['fk', __tablename__, 'transaction_id'])),
            nullable = False),
        Column('offset', SmallInteger, nullable=False),
        Column('amount', BigInteger, nullable=False),
        Column('contract', BitcoinScript, nullable=False),
        PrimaryKeyConstraint('transaction_id', 'offset',
            name = '__'.join(['pk', __tablename__])),
        CheckConstraint(
            (0 <= sql.column('amount')) &
            (sql.column('amount') <= 9007199254740991), # 2^53 - 1
            name = '__'.join(['ck', __tablename__, 'amount'])),
        Index('__'.join(['ix', __tablename__, 'contract']), 'contract'),)

    # Input
    __tablename__ = __tableprefix__ + 'input'
    op.create_table(__tableprefix__,
        Column('transaction_id', Integer,
            ForeignKey(__tableprefix__ + 'transaction.id',
                name = '__'.join(['fk', __tablename__, 'transaction_id'])),
            nullable = False),
        Column('offset', SmallInteger, nullable=False),
        Column('hash', Hash256, nullable=False),
        Column('index', UnsignedInteger, nullable=False),
        Column('output_id', Integer,
            ForeignKey(__tableprefix__ + 'output.id',
                name = '__'.join(['fk', __tablename__]))),
        Column('endorsement', BitcoinScript, nullable=False),
        Column('sequence', UnsignedInteger, nullable=False),
        PrimaryKeyConstraint('transaction_id', 'offset',
            name = '__'.join(['pk', __tablename__])),
        Index('__'.join(['ix', __tablename__, 'hash', 'index']),
            'hash', 'index'),)

    # BlockTransactionListNode
    __tablename__ = __tableprefix__ + 'block_transaction_list_node'
    op.create_table(__tablename__,
        Column('block_id', Integer,
            ForeignKey(__tableprefix__ + 'block.id',
                name = '__'.join(['fk', __tablename__, 'block_id'])),
            nullable = False),
        Column('offset', SmallInteger, nullable=False),
        Column('transaction_id', Integer,
            ForeignKey(__tableprefix__ + 'transaction.id',
                name = '__'.join(['fk', __tablename__, 'transaction_id'])),
            nullable = False),
        PrimaryKeyConstraint('block_id', 'offset',
            name = '__'.join(['pk', __tablename__])),
        Index('__'.join(['ix',__tablename__,'transaction_id']),
            'transaction_id'),)

    # ConnectedBlockInfo
    __tablename__ = __tableprefix__ + 'connected_block_info'
    op.create_table(__tablename__,
        Column('block_id', Integer,
            ForeignKey(__tableprefix__ + 'block.id',
                name = '__'.join(['fk', __tablename__, 'block_id']))),
        Column('parent_id', Integer,
            ForeignKey(__tableprefix__ + 'block.id',
                name = '__'.join(['fk', __tablename__, 'parent_id']))),
        Column('height', Integer, nullable=False),
        Column('aggregate_work', Numeric(31,0), nullable=False),
        PrimaryKeyConstraint('block_id',
            name = '__'.join(['pk', __tablename__])),
        Index('__'.join(['ix', __tablename__, 'height']),
            'height'),
        Index('__'.join(['ix', __tablename__, 'aggregate_work']),
            'aggregate_work'),
        CheckConstraint(0 <= sql.column('height'),
            name = '__'.join(['ck', __tablename__, 'height'])),
        CheckConstraint(1 <= sql.column('aggregate_work'),
            name = '__'.join(['ck', __tablename__, 'aggregate_work'])),)

def downgrade():
    op.drop_table(__tableprefix__ + 'connected_block_info')
    op.drop_table(__tableprefix__ + 'block_transaction_list_node')
    op.drop_table(__tableprefix__ + 'input')
    op.drop_table(__tableprefix__ + 'output')
    op.drop_table(__tableprefix__ + 'transaction')
    op.drop_table(__tableprefix__ + 'block')
    op.drop_table(__tableprefix__ + 'checkpoint')
    op.drop_table(__tableprefix__ + 'chain')
