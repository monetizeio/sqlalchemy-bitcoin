# -*- coding: utf-8 -*-

# SQLAlchemy object-relational mapper
from sqlalchemy import *

from bitcoin.serialize import (
    serialize_leint, deserialize_leint,
    serialize_beint, deserialize_beint)
from bitcoin.tools import StringIO

class LittleEndian(TypeDecorator):
    impl = LargeBinary

    def __init__(self, length=None, *args, **kwargs):
        super(LittleEndian, self).__init__(length, *args, **kwargs)

    def process_bind_param(self, value, dialect):
        return serialize_leint(value, self.impl.length)
    def process_result_value(self, value, dialect):
        return deserialize_leint(StringIO(value), len(value))
    def copy(self):
        return self.__class__(self.impl.length)

class BigEndian(TypeDecorator):
    impl = LargeBinary

    def __init__(self, length=None, *args, **kwargs):
        super(BigEndian, self).__init__(length, *args, **kwargs)

    def process_bind_param(self, value, dialect):
        return serialize_beint(value, self.impl.length)
    def process_result_value(self, value, dialect):
        return deserialize_beint(StringIO(value), len(value))
    def copy(self):
        return self.__class__(self.impl.length)

class UnsignedSmallInteger(TypeDecorator):
    impl = SmallInteger

    def process_bind_param(self, value, dialect):
        return (value >= 2**15) and value - 2**16 or value
    def process_result_value(self, value, dialect):
        return (value < 0) and value + 2**16 or value

class UnsignedInteger(TypeDecorator):
    impl = Integer

    def process_bind_param(self, value, dialect):
        return (value >= 2**31) and value - 2**32 or value
    def process_result_value(self, value, dialect):
        return (value < 0) and value + 2**32 or value

class UnsignedBigInteger(TypeDecorator):
    impl = BigInteger

    def process_bind_param(self, value, dialect):
        return (value >= 2**63) and value - 2**64 or value
    def process_result_value(self, value, dialect):
        return (value < 0) and value + 2**64 or value
