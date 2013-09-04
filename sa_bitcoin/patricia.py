# -*- coding: utf-8 -*-

# SQLAlchemy object-relational mapper
from sqlalchemy import *
from sqlalchemy import orm
from . import Base

from .fields.hash_ import Hash256
from .mixins.hashable import HybridHashableMixin

from bitcoin import patricia as core

class PatriciaNode(HybridHashableMixin, core.PatriciaNode, Base):
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

    extra = Column(LargeBinary)

    children = orm.relationship(lambda: PatriciaLink,
        secondary     = lambda: PatriciaNodeLink.__table__,
        primaryjoin   = lambda: PatriciaNode.id == PatriciaNodeLink.parent_id,
        secondaryjoin = lambda: PatriciaLink.id == PatriciaNodeLink.link_id,
        order_by      = lambda: PatriciaLink.prefix)
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
