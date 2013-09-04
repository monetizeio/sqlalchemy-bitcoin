# -*- coding: utf-8 -*-

# SQLAlchemy object-relational mapper
from sqlalchemy import *
from sqlalchemy import orm
from . import Base

from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.orderinglist import ordering_list

from .fields.hash_ import Hash256
from .fields.integer import UnsignedInteger
from .fields.script import BitcoinScript
from .fields.time_ import BlockTime, UNIXDateTime
from .mixins.hashable import HybridHashableMixin

from bitcoin import core

class Chain(Base):
    __tablename__ = 'bitcoin_chain'
    __table_args__ = (
        Index('__'.join(['ix',__tablename__,'name']),
            'name', unique = True),
        Index('__'.join(['ix',__tablename__,'genesis_hash']),
            'genesis_hash', unique = True),)
    id = Column(Integer,
        Sequence('__'.join([__tablename__,'id','seq'])),
        primary_key = True)

    name = Column(String(48), nullable=False)

    magic = Column(LargeBinary(4), nullable=False)

    port = Column(SmallInteger,
        CheckConstraint('1 <= port and port <= 65535'),
        nullable = False)

    genesis = Column(LargeBinary(80), nullable=False, unique=True)
    genesis_hash = Column(Hash256, nullable=False)

    testnet = Column(Boolean, nullable=False)

    pubkey_hash_prefix = Column(SmallInteger, nullable=False)
    script_hash_prefix = Column(SmallInteger, nullable=False)
    secret_prefix = Column(SmallInteger, nullable=False)

class Checkpoint(Base):
    __tablename__ = 'bitcoin_checkpoint'
    __table_args__ = (
        Index('__'.join(['ix',__tablename__,'hash']),
            'chain_id', 'height', unique=True),)
    id = Column(Integer,
        Sequence('__'.join([__tablename__,'id','seq'])),
        primary_key = True)

    chain_id = Column(Integer, ForeignKey('bitcoin_chain.id'), nullable=False)
    chain = orm.relationship(lambda: Chain, backref='checkpoints')

    height = Column(Integer, nullable=False)

    hash = Column(Hash256, nullable=False)
    coins = Column(UnsignedInteger, nullable=False)
    outputs = Column(UnsignedInteger, nullable=False)

class Block(HybridHashableMixin, core.Block, Base):
    __tablename__ = 'bitcoin_block'
    __table_args__ = (
        Index('__'.join(['ix',__tablename__,'hash']),
            'hash', unique = True),)
    __lazy_slots__ = ('hash',)
    id = Column(Integer,
        Sequence('__'.join([__tablename__,'id','seq'])),
        primary_key = True)

    # The serialization version.
    # Allowed values are 1 (original) and 2 (BIP 34).
    version = Column(SmallInteger, nullable=False)

    @orm.validates('version')
    def version_range(self, key, version):
        assert version in (1,2)
        return version

    # Called ‘parent’ because this is technically a branching/tree relationship,
    # this field is called called the ‘previous block’ in the bitcoin protocol as
    # it represent the last block in the nominally linear chain.
    parent_hash = Column(Hash256, nullable=False)

    # The hash of the root node of the Block/Transaction merkle list recording
    # the transactions confirmed by this block.
    merkle_hash = Column(Hash256, nullable=False)

    # Set by the solo miner/mine pool operator, this is the self-reported
    # generation time for the block header (within the uncertainty allowed
    # by the bitcoin protocol).
    time = Column(UNIXDateTime, nullable=False)

    # The difficulty of the block, which is determined by the bitcoin protocol
    # and in turn sets the threshold target which a hash must meet in order to
    # be a valid proof-of-work.
    # Subject to the constraint: 0x01010000 <= bits <= 0x1d00ffff
    bits = Column(Integer,
        CheckConstraint('16842752 <= bits and bits <= 486604799'),
        nullable = False)

    # An information-free value set by the miner/mine pool operator so as to
    # make the block hash less than the target value, thereby proving work done
    # in order to derive an appropriate value.
    nonce = Column(UnsignedInteger, nullable=False)

    # The digest value which results from applying the proof-of-work function
    # to the serial representation of this block.
    _hash = Column('hash', Hash256, nullable=False)

    # A one-to-one relationship recording information derived from the block
    # connection. The information is not contained within the block structure
    # itself because blocks may be received out of order or many-at-a-time,
    # and therefore this information may not be available at the time the
    # block is inserted into the database.
    info = orm.relationship(lambda: ConnectedBlockInfo,
        primaryjoin = 'Block.id == ConnectedBlockInfo.block_id',
        uselist     = False)

    # The list of transactions is stored in a many-to-many relationship with
    # an intermediary ordering field. We use SQLAlchemy's ordering_list and
    # association_proxy extensions to make the transactions accessible as a
    # list-like object.
    transaction_list_nodes = orm.relationship(lambda: BlockTransactionListNode,
        collection_class = ordering_list('position'),
        order_by         = lambda: BlockTransactionListNode.position)
    transactions = association_proxy('transaction_list_nodes', 'transaction',
        creator = lambda tx: BlockTransactionListNode(transaction=tx))

class BlockTransactionListNode(Base):
    __tablename__ = 'bitcoin_block_transaction_list_node'
    __table_args__ = (
        Index('__'.join(['ix',__tablename__,'block_id','position']),
            'block_id', 'position', unique = True),
        Index('__'.join(['ix',__tablename__,'transaction_id']),
            'transaction_id'),)
    id = Column(Integer,
        Sequence('__'.join([__tablename__,'id','seq'])),
        primary_key = True)

    block_id = Column(Integer, ForeignKey('bitcoin_block.id'), nullable=False)
    block = orm.relationship(lambda: Block)

    position = Column(SmallInteger, nullable=False)

    transaction_id = Column(Integer,
        ForeignKey('bitcoin_transaction.id'),
        nullable = False)
    transaction = orm.relationship(lambda: Transaction)

class Transaction(HybridHashableMixin, core.Transaction, Base):
    __tablename__ = 'bitcoin_transaction'
    __table_args__ = (
        Index('__'.join(['ix',__tablename__,'hash']),
            'hash', unique = True),)
    __lazy_slots__ = ('hash',)
    id = Column(Integer,
        Sequence('__'.join([__tablename__,'id','seq'])),
        primary_key = True)

    # The serialization version.
    # Allowed values are 1 (original) and 2 (nRefHeight).
    version = Column(SmallInteger, nullable=False)

    @orm.validates('version')
    def version_range(self, key, version):
        assert version in (1,2)
        return version

    # The inputs and outputs are joined from a separate models using the
    # ordering_list collection class, which maintains the position index.
    # The create_inputs() and create_outputs() methods are necessary to
    # override python-bitcoin's default behavior which itself would
    # override the SQLAlchemy collection classes.
    inputs = orm.relationship(lambda: Input,
        collection_class = ordering_list('position'),
        order_by         = lambda: Input.position)
    def create_inputs(self):
        pass

    outputs = orm.relationship(lambda: Output,
        collection_class = ordering_list('position'),
        order_by         = lambda: Output.position)
    def create_outputs(self):
        pass

    # The lock time is either a block height or UNIX timestamp, and a transaction
    # is prevented from becoming part of the block chain until the specific time
    # has passed or a specified block height has been reached. In either cases,
    # the comparison is strictly greater-than: the block height or time needs to
    # have been exceeded before the transaction can make it on the chain.
    lock_time = Column(BlockTime, nullable=False)

    # The reference height is added in nVersion=2 transactions, and is the block
    # height used for interest / demurrage time-value adjustments. It has no
    # meaning for other transaction versions, where it assume the default value
    # of zero.
    reference_height = Column(Integer, nullable=False)

    @orm.validates('reference_height')
    def version_range(self, key, reference_height):
        if self.version not in (2,):
            assert reference_height == 0
        return reference_height

    # The digest value which results from applying the double-SHA256 function
    # to the serial representation of this transaction.
    _hash = Column('hash', Hash256, nullable=False)

class Output(core.Output, Base):
    __tablename__ = 'bitcoin_output'
    __table_args__ = (
        Index('__'.join(['ix',__tablename__,'transaction_id','position']),
            'transaction_id', 'position', unique = True),)
    id = Column(Integer,
        Sequence('__'.join([__tablename__,'id','seq'])),
        primary_key = True)

    transaction_id = Column(Integer,
        ForeignKey('bitcoin_transaction.id'),
        nullable = False)
    transaction = orm.relationship(lambda: Transaction)

    position = Column(SmallInteger, nullable=False)

    # Subject to the constraint: 0 <= amount <= 2^53 - 1
    amount = Column(BigInteger,
        CheckConstraint('0 <= amount and amount <= 9007199254740991'),
        nullable = False)

    contract = Column(BitcoinScript, nullable=False)
Transaction.output_class = Output

class Input(core.Input, Base):
    __tablename__ = 'bitcoin_input'
    __table_args__ = (
        Index('__'.join(['ix',__tablename__,'transaction_id','position']),
            'transaction_id', 'position', unique = True),)
    id = Column(Integer,
        Sequence('__'.join([__tablename__,'id','seq'])),
        primary_key = True)

    transaction_id = Column(Integer,
        ForeignKey('bitcoin_transaction.id'),
        nullable = False)
    transaction = orm.relationship(lambda: Transaction)

    position = Column(SmallInteger, nullable=False)

    hash = Column(Hash256, nullable=False)

    index = Column(UnsignedInteger, nullable=False)

    is_coinbase = hybrid_property(core.Input.is_coinbase.fget,
                                  core.Input.is_coinbase.fset,
                                  core.Input.is_coinbase.fdel)
    @is_coinbase.expression
    def is_coinbase(cls):
        return ((cls.hash  == 0) &
                (cls.index == 0xffffffff))

    output_id = Column(Integer, ForeignKey('bitcoin_output.id'))
    output = orm.relationship(lambda: Output)

    endorsement = Column(BitcoinScript, nullable=False)

    sequence = Column(UnsignedInteger, nullable=False)
Transaction.input_class = Input

class ConnectedBlockInfo(core.ConnectedBlockInfo, Base):
    __tablename__ = 'bitcoin_connected_block_info'
    __table_args__ = (
        Index('__'.join(['ix',__tablename__,'height']),
            'height'),
        Index('__'.join(['ix',__tablename__,'aggregate_work']),
            'aggregate_work'),)
    def __init__(self, *args, **kwargs):
        return Base.__init__(self, *args, **kwargs)

    block_id = Column(Integer,
        ForeignKey('bitcoin_block.id'),
        primary_key = True)
    block = orm.relationship(lambda: Block,
        primaryjoin = 'Block.id == ConnectedBlockInfo.block_id')

    parent_id = Column(Integer, ForeignKey('bitcoin_block.id'))
    parent = orm.relationship(lambda: Block,
        primaryjoin = 'Block.id == ConnectedBlockInfo.parent_id')

    height = Column(Integer,
        CheckConstraint('0 <= height'),
        nullable = False)

    aggregate_work = Column(Numeric(31,0),
        CheckConstraint('0 < aggregate_work'),
        nullable = False)

    txid_index_id = Column(Integer,
        ForeignKey('bitcoin_patricia_node.id'),
        nullable = False)
    txid_index = orm.relationship(lambda: TxIdIndex,
        primaryjoin = 'PatriciaNode.id == ConnectedBlockInfo.txid_index_id')

    contract_index_id = Column(Integer,
        ForeignKey('bitcoin_patricia_node.id'),
        nullable = False)
    contract_index = orm.relationship(lambda: ContractIndex,
        primaryjoin = 'PatriciaNode.id == ConnectedBlockInfo.contract_index_id')

from .ledger import TxIdIndex, ContractIndex
