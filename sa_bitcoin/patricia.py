# -*- coding: utf-8 -*-

# SQLAlchemy object-relational mapper
from sqlalchemy import *
from sqlalchemy import orm
from . import Base

from .fields.binary import BitField
from .fields.hash_ import Hash256
from .mixins.hashable import HybridHashableMixin

from bitcoin import patricia as core
from bitcoin.tools import Bits

class PatriciaNode(HybridHashableMixin, core.PatriciaNode, Base):
    __slots__ = ('value prune_value '
                 'left_prefix left_node left_hash '
                 'right_prefix right_node right_hash '
                 '_hash size length').split()
    __tablename__ = 'bitcoin_patricia_node'
    __table_args__ = (
        Index('__'.join(['ix',__tablename__,'hash']),
            'hash'),)
    __lazy_slots__ = ('hash',)
    id = Column(Integer,
        Sequence('__'.join([__tablename__,'id','seq'])),
        primary_key = True)

    type = Column(
        Enum('txid_index', 'contract_index',
            name = '__'.join([__tablename__,'type','enum'])),
        nullable = False)
    __mapper_args__ = {
        'polymorphic_on': type,
    }

    value = Column(LargeBinary)
    prune_value = Column(Boolean)

    left_prefix  = Column(BitField(implicit=Bits('0b0')))
    left_node_id = Column(Integer, ForeignKey('bitcoin_patricia_node.id'))
    left_node    = orm.relationship(lambda: PatriciaNode,
        primaryjoin = 'PatriciaNode.id == PatriciaNode.left_node_id',
        uselist     = False)
    left_hash    = Column(Hash256(length=32))

    right_prefix  = Column(BitField(implicit=Bits('0b1')))
    right_node_id = Column(Integer, ForeignKey('bitcoin_patricia_node.id'))
    right_node    = orm.relationship(lambda: PatriciaNode,
        primaryjoin = 'PatriciaNode.id == PatriciaNode.right_node_id',
        uselist     = False)
    right_hash    = Column(Hash256(length=32))

    @property
    def children(self):
        link_class = getattr(self, 'get_link_class',
            lambda: getattr(self, 'link_class', core.PatriciaLink))()
        class _Children(list):
            def append(children, link):
                if not link.prefix[0]:
                    self.left_prefix, self.left_node, self.left_hash = (
                        link.prefix, link.node, link._hash)
                else:
                    self.right_prefix, self.right_node, self.right_hash = (
                        link.prefix, link.node, link._hash)
            def extend(children, links):
                for link in links:
                    children.append(link)
        children = ()
        if self.left_prefix is not None:
            children += (link_class(
                prefix = self.left_prefix,
                node   = self.left_node,
                hash   = self.left_hash),)
        if self.right_prefix is not None:
            children += (link_class(
                prefix = self.right_prefix,
                node   = self.right_node,
                hash   = self.right_hash),)
        return _Children(children)
    def children_create(self):
        pass

    # The digest value which results from applying the double-SHA256 function
    # to the serial representation of this node.
    _hash = Column('hash', Hash256(length=32), nullable=False)

    size = Column(Integer, nullable=False)

    length = Column(Integer, nullable=False)
PatriciaNode.node_class = PatriciaNode

class PatriciaLink(HybridHashableMixin, core.PatriciaLink, Base):
    __tablename__ = 'bitcoin_patricia_link'
    __table_args__ = (
        Index('__'.join(['ix',__tablename__,'node_id']),
            'node_id'),
        Index('__'.join(['ix',__tablename__,'prefix']),
            'prefix'),)
    __lazy_slots__ = ('hash',)
    id = Column(Integer,
        Sequence('__'.join([__tablename__,'id','seq'])),
        primary_key = True)

    prefix = Column(LargeBinary, nullable=False)

    @orm.validates('prefix')
    def prefix_length(self, key, prefix):
        assert len(prefix) >= 1
        return prefix

    node_id = Column(Integer,
        ForeignKey('bitcoin_patricia_node.id'),
        nullable = False)
    node = orm.relationship(lambda: PatriciaNode)

    _hash = Column('hash', Hash256(length=32), nullable=False)
PatriciaNode.link_class = PatriciaLink

class PatriciaNodeLink(Base):
    __tablename__ = 'bitcoin_patricia_node_link'
    __table_args__ = (
        Index('__'.join([__tablename__,'parent_id','link_id']),
            'parent_id', 'link_id', unique = True),)
    id = Column(Integer,
        Sequence('__'.join([__tablename__,'id','seq'])),
        primary_key = True)

    parent_id = Column(Integer,
        ForeignKey('bitcoin_patricia_node.id'),
        index = True, nullable = False)
    parent = orm.relationship(lambda: PatriciaNode)

    link_id = Column(Integer,
        ForeignKey('bitcoin_patricia_link.id'),
        index = True, nullable = False)
    link = orm.relationship(lambda: PatriciaLink)
