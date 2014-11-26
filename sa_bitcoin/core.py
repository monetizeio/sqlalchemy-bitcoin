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

__tableprefix__ = 'bitcoin_'

class ReplMixin(object):
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
        return ('<' + self.__class__.__module__ +
                '.' + self.__class__.__name__   +
                ' ' + str(self) + '>')

class Chain(ReplMixin, Base):
    __tablename__ = __tableprefix__ + 'chain'

    # An auto-incrementing integer primary key is used because most core
    # objects point to their chain so there is benefit to keeping foreign
    # keys small, and chains are not supposed to be lightweight objects,
    # so we should not expect lock contention.
    id = Column(Integer,
        Sequence('__'.join(['sq', __tablename__, 'id'])),
        nullable = False)

    # The magic bytes prefix messages in the peer-to-peer protocol and some
    # on-disk data structures. These values are typically randomly chosen and
    # serve merely to keep separate bitcoin networks from communicating.
    magic = Column(LargeBinary(4), nullable=False)

    # The port is the default TCP/IP port for the peer-to-peer protocol. Nodes
    # do not have to use the default port setting, and the actual port is
    # specified in address messages.
    port = Column(UnsignedSmallInteger, nullable=False)

    # The genesis block and its SHA-256^2 hash. Chains are chiefly identified
    # by the SHA-256^2 hash of their genesis block, which should be different
    # for every chain (and is different for every chain that matters).
    genesis = Column(LargeBinary(80), nullable=False)
    genesis_hash = Column(Hash256, nullable=False)

    # The payload version prefixes used to indicate whether the payload type.
    pubkey_hash_prefix = Column(SmallInteger, nullable=False)
    script_hash_prefix = Column(SmallInteger, nullable=False)
    secret_prefix = Column(SmallInteger, nullable=False)

    # There are many common ways in which testnet chains differ from their
    # mainnet counterparts (e.g. difficulty adjustment, IsStandard checks).
    # Rather than require a separate logic, we encode testnet status in the
    # chain definition so the validation code can be shared between both
    # chains.
    is_testnet = Column(Boolean, nullable=False)

    __table_args__ = (
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

    def __unicode__(self):
        return serialize_hash(self.genesis_hash).encode('hex').decode('ascii')

class Checkpoint(ReplMixin, Base):
    __tablename__ = __tableprefix__ + 'checkpoint'

    # Join keys linking us to the chain this checkpoint is recording:
    chain_id = Column(Integer,
        ForeignKey(__tableprefix__ + 'chain.id',
            name = '__'.join(['fk', __tablename__, 'chain'])),
        nullable = False)

    # Checkpoints are recorded hashes at a specific height.
    height = Column(Integer, nullable=False)

    # The SHA-256^2 hash value of the checkpoint.
    hash = Column(Hash256, nullable=False)

    # FIXME: The ultraprune branch of bitcoin records the number of unspent
    # transactions, called 'coins'. The upcoming authenticated prefix tree
    # validation index changes this to record individual outputs, for the
    # purpose of minimizing proof size. We need to choose one of the
    # following based on what approach we take, but not both.
    #coins = Column(Integer, nullable=False)
    #outputs = Column(Integer, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('chain_id', 'height',
            name = '__'.join(['pk', __tablename__])),
        CheckConstraint(0 <= sql.column('height'),
            name = '__'.join(['ck', __tablename__, 'height'])),)
        #CheckConstraint('0 <= coins and coins <= outputs',
        #    name = '__'.join(['ck', __tablename__, 'utxo'])),

    chain = orm.relationship(lambda: Chain,
        backref = orm.backref('checkpoints',
            order_by = lambda: Checkpoint.height))

    def __unicode__(self):
        return (unicode(self.chain)  + u" "  +
                unicode(self.height) + u": " +
                serialize_hash(self.hash).encode('hex').decode('ascii'))

class Block(HybridHashableMixin, core.Block, Base):
    __tablename__ = __tableprefix__ + 'block'

    # The natural primary key is the SHA-256^2 hash of the block header,
    # otherwise known as the proof-of-work, however hash is stored as a
    # BLOB on some SQL architectures which do not allow binary objects
    # within foreign-key constraints. So we use a simple auto-incrementing
    # integer instead:
    id = Column(Integer,
        Sequence('__'.join(['sq', __tablename__, 'id'])),
        nullable = False)

    # The hard-fork version.
    # Known values are 0 (original).
    format = Column(SmallInteger, nullable=False)

    @orm.validates('format')
    def format_range(self, key, format):
        assert format in (0,)
        return format

    # The soft-fork version.
    # Known values are 1 (original) and 2 (BIP 34).
    version = Column(UnsignedInteger, nullable=False)

    # Called ‘parent’ because this is technically a branching/tree relationship,
    # this field is called called the ‘previous block’ in the bitcoin protocol as
    # it represents the last block in the nominally linear chain.
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
    bits = Column(Integer, nullable=False)

    # An information-free value set by the miner/mine pool operator so as to
    # make the block hash less than the target value, thereby proving work done
    # in order to derive an appropriate value.
    nonce = Column(UnsignedInteger, nullable=False)

    # The digest value which results from applying the proof-of-work function
    # to the serial representation of this block.
    _hash = Column('hash', Hash256, nullable=False)

    __lazy_slots__ = ('hash',)
    __table_args__ = (
        PrimaryKeyConstraint('id',
            name = '__'.join(['pk', __tablename__])),
        Index('__'.join(['ix', __tablename__, 'hash']),
            'hash', unique = True),
        CheckConstraint(
            (16842752 <= sql.column('bits')) & (sql.column('bits') <= 486604799),
            name = '__'.join(['ck', __tablename__, 'bits'])),)

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
        collection_class = ordering_list('offset'),
        order_by         = lambda: BlockTransactionListNode.offset)
    transactions = association_proxy('transaction_list_nodes', 'transaction',
        creator = lambda tx: BlockTransactionListNode(transaction=tx))

class BlockTransactionListNode(Base, ReplMixin):
    __tablename__ = __tableprefix__ + 'block_transaction_list_node'

    block_id = Column(Integer,
        ForeignKey(__tableprefix__ + 'block.id',
            name = '__'.join(['fk', __tablename__, 'block_id'])),
        nullable = False)

    offset = Column(SmallInteger, nullable=False)

    transaction_id = Column(Integer,
        ForeignKey(__tableprefix__ + 'transaction.id',
            name = '__'.join(['fk', __tablename__, 'transaction_id'])),
        nullable = False)

    __table_args__ = (
        PrimaryKeyConstraint('block_id', 'offset',
            name = '__'.join(['pk', __tablename__])),
        Index('__'.join(['ix',__tablename__,'transaction_id']),
            'transaction_id'),)

    block = orm.relationship(lambda: Block)
    transaction = orm.relationship(lambda: Transaction)

class Transaction(HybridHashableMixin, core.Transaction, Base):
    __tablename__ = __tableprefix__ + 'transaction'

    # The natural primary key is SHA-256^2 hash of the serialized transaction,
    # otherwise known as the txid, however hash is stored as a BLOB on some
    # SQL architectures which do not allow binary objects within foreign-key
    # constraints. So we use a simple auto-incrementing integer instead:
    id = Column(Integer, Sequence('__'.join(['sq', __tablename__])))

    # The hard-fork version.
    # Known values are 0 (original) and 1 (refheight).
    format = Column(SmallInteger, nullable=False)

    @orm.validates('format')
    def format_range(self, key, format):
        assert format in (0,1)
        return format

    # The soft-fork version.
    # Known values are 1 (original).
    version = Column(UnsignedInteger, nullable=False)

    # The lock time is either a block height or UNIX timestamp, and a transaction
    # is prevented from becoming part of the block chain until the specific time
    # has passed or a specified block height has been reached. In either cases,
    # the comparison is strictly greater-than: the block height or time needs to
    # have been exceeded before the transaction can make it on the chain.
    lock_time = Column(BlockTime, nullable=False)

    # The reference height is added in Freicoin transactions, and is the block
    # height used for interest / demurrage time-value adjustments. Outside of
    # this context it has no meaning and assumes the default value of zero.
    reference_height = Column(UnsignedInteger, nullable=False)

    # The digest value which results from applying the double-SHA256 function
    # to the serial representation of this transaction.
    _hash = Column('hash', Hash256, nullable=False)

    __lazy_slots__ = ('hash',)
    __table_args__ = (
        PrimaryKeyConstraint('id',
            name = '__'.join(['pk', __tablename__])),
        Index('__'.join(['ix', __tablename__, 'hash']),
            'hash', unique = True),)

    # The inputs and outputs are joined from separate models using the
    # ordering_list collection class, which maintains the offset index.
    # The create_inputs() and create_outputs() methods are necessary to
    # override python-bitcoin's default behavior which itself would
    # override the SQLAlchemy collection classes.
    inputs = orm.relationship(lambda: Input,
        collection_class = ordering_list('offset'),
        order_by         = lambda: Input.offset)
    def create_inputs(self):
        pass

    outputs = orm.relationship(lambda: Output,
        collection_class = ordering_list('offset'),
        order_by         = lambda: Output.offset)
    def create_outputs(self):
        pass

class Output(core.Output, Base):
    __tablename__ = __tableprefix__ + 'output'

    # Identification of the transaction containing this output, and
    # the index within its output list (vout in the Satoshi client).
    transaction_id = Column(Integer,
        ForeignKey(__tableprefix__ + 'transaction.id',
            name = '__'.join(['fk', __tablename__, 'transaction_id'])),
        nullable = False)
    offset = Column(SmallInteger, nullable=False)

    # Subject to the constraint: 0 <= amount <= 2^53 - 1
    # NOTE: See the Freimarkets whitepaper for an explanation of the
    #   constant 2^53 - 1.
    amount = Column(BigInteger, nullable=False)

    # What the Satoshi client calls scriptPubKey:
    contract = Column(BitcoinScript, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('transaction_id', 'offset',
            name = '__'.join(['pk', __tablename__])),
        CheckConstraint(
            (0 <= sql.column('amount')) &
            (sql.column('amount') <= 9007199254740991), # 2^53 - 1
            name = '__'.join(['ck', __tablename__, 'amount'])),
        Index('__'.join(['ix', __tablename__, 'contract']), 'contract'),)

    transaction = orm.relationship(lambda: Transaction)
Transaction.output_class = Output

class Input(core.Input, Base):
    __tablename__ = __tableprefix__ + 'input'

    # Identification of the transaction containing this input, and
    # the index within its input list (vin in the Satoshi client).
    transaction_id = Column(Integer,
        ForeignKey(__tableprefix__ + 'transaction.id',
            name = '__'.join(['fk', __tablename__, 'transaction_id'])),
        nullable = False)
    offset = Column(SmallInteger, nullable=False)

    # Identification of the transaction containing this output, and
    # the index within its output list.
    hash = Column(Hash256, nullable=False)
    index = Column(UnsignedInteger, nullable=False)
    output_id = Column(Integer,
        ForeignKey(__tableprefix__ + 'output.id',
            name = '__'.join(['fk', __tablename__])))

    # What the Satoshi client calls scriptSig:
    endorsement = Column(BitcoinScript, nullable=False)

    # An integer field intended for use with transaction replacement,
    # typically set to 0xffffffff to indicate a final transaction:
    sequence = Column(UnsignedInteger, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('transaction_id', 'offset',
            name = '__'.join(['pk', __tablename__])),
        Index('__'.join(['ix', __tablename__, 'hash', 'index']),
            'hash', 'index'),)

    transaction = orm.relationship(lambda: Transaction)
    output = orm.relationship(lambda: Output)

    is_coinbase = hybrid_property(core.Input.is_coinbase.fget,
                                  core.Input.is_coinbase.fset,
                                  core.Input.is_coinbase.fdel)
    @is_coinbase.expression
    def is_coinbase(cls):
        return ((cls.hash  == 0) &
                (cls.index == 0xffffffff))
Transaction.input_class = Input

class ConnectedBlockInfo(core.ConnectedBlockInfo, Base):
    __tablename__ = __tableprefix__ + 'connected_block_info'

    block_id = Column(Integer,
        ForeignKey(__tableprefix__ + 'block.id',
            name = '__'.join(['fk', __tablename__, 'block_id'])))

    parent_id = Column(Integer,
        ForeignKey(__tableprefix__ + 'block.id',
            name = '__'.join(['fk', __tablename__, 'parent_id'])))

    height = Column(Integer, nullable=False)

    aggregate_work = Column(Numeric(31,0), nullable=False)

    __table_args__ = (
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

    block = orm.relationship(lambda: Block,
        primaryjoin = 'Block.id == ConnectedBlockInfo.block_id')
    parent = orm.relationship(lambda: Block,
        primaryjoin = 'Block.id == ConnectedBlockInfo.parent_id')

    def __init__(self, *args, **kwargs):
        return Base.__init__(self, *args, **kwargs)
